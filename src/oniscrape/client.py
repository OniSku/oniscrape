import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar
from urllib.parse import urlparse

from curl_cffi.requests import AsyncSession, Response
from pydantic import BaseModel
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import ScraperConfig
from .cookies.base import BaseCookieStorage
from .cookies.memory import InMemoryCookieStorage
from .extractors.generic import extract_json_ld
from .extractors.meta import extract_relay_cache
from .extractors.nextjs import extract_next_data
from .extractors.nuxt import extract_nuxt_data
from .pipeline.schema_mapper import map_state_to_model
from .proxy.manager import ProxyManager
from .result import ScrapeResult

T = TypeVar("T", bound=BaseModel)


class ScraperRequestError(Exception):
    """Исключение сетевого сбоя или блокировки антифродом."""

    def __init__(self, message: str, status_code: int | None = None, url: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class ScraperClient:
    """Асинхронный клиент для парсинга с поддержкой curl_cffi, TLS-фингерпринтов,
    изоляции прокси-сессий, пула impersonate и автоматических ретраев.
    """

    def __init__(
        self,
        config: ScraperConfig | None = None,
        proxy_manager: ProxyManager | None = None,
        cookie_storage: BaseCookieStorage | None = None,
    ):
        self.config = config or ScraperConfig()
        self.proxy_manager = proxy_manager or (
            ProxyManager(self.config.proxy) if self.config.proxy.urls else None
        )
        self.cookie_storage = cookie_storage or InMemoryCookieStorage()

    @classmethod
    def from_cookies(
        cls,
        cookies: dict[str, str],
        domain: str = "",
        config: ScraperConfig | None = None,
        proxy_manager: ProxyManager | None = None,
    ) -> "ScraperClient":
        """Создает ScraperClient с предзагруженным словарем куки авторизации."""
        storage = InMemoryCookieStorage(initial_cookies={domain: cookies.copy()})
        return cls(config=config, proxy_manager=proxy_manager, cookie_storage=storage)

    @classmethod
    def from_cookies_file(
        cls,
        filepath: str,
        domain: str = "",
        config: ScraperConfig | None = None,
        proxy_manager: ProxyManager | None = None,
    ) -> "ScraperClient":
        """Создает ScraperClient с автоматической загрузкой куки из файла (.json или cookies.txt).

        Поддерживает экспорт из браузерных расширений (Cookie-Editor, EditThisCookie).
        """
        from .cookies.loader import load_cookies_from_file

        cookies = load_cookies_from_file(filepath)
        return cls.from_cookies(
            cookies=cookies,
            domain=domain,
            config=config,
            proxy_manager=proxy_manager,
        )

    async def __aenter__(self) -> "ScraperClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    @asynccontextmanager
    async def create_session(
        self,
        proxy: str | None = None,
        impersonate: str | None = None,
        custom_headers: dict[str, str] | None = None,
    ) -> AsyncIterator[AsyncSession]:
        """Создает изолированную сессию под конкретный прокси с гарантированным
        закрытием сокетов libcurl по завершении блока.
        """
        target_impersonate = impersonate or self.config.default_impersonate

        headers = self.config.headers.copy()
        if custom_headers:
            headers.update(custom_headers)

        session = AsyncSession(
            impersonate=target_impersonate,
            proxy=proxy,
            headers=headers if headers else None,
            verify=self.config.verify_ssl,
            timeout=self.config.timeout_seconds,
        )
        try:
            yield session
        finally:
            await session.close()

    async def request(
        self,
        method: str,
        url: str,
        impersonate: str | None = None,
        proxy: str | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json: Any = None,
        **kwargs: Any,
    ) -> Response:
        """Выполняет HTTP-запрос с автоматическим выбором прокси из пула, ротацией
        TLS-фингерпринтов при повторах и умными ретраями.
        """
        retry_cfg = self.config.retry
        domain = urlparse(url).netloc

        retrying = AsyncRetrying(
            stop=stop_after_attempt(retry_cfg.max_attempts),
            wait=wait_exponential(
                multiplier=retry_cfg.min_backoff_seconds,
                max=retry_cfg.max_backoff_seconds,
            ),
            retry=retry_if_exception_type((ScraperRequestError, Exception)),
            reraise=True,
        )

        async for attempt in retrying:
            with attempt:
                # Выбираем прокси для текущей попытки
                current_proxy = proxy
                if current_proxy is None and self.proxy_manager:
                    current_proxy = self.proxy_manager.get_proxy()

                # Выбираем TLS-фингерпринт (ротация из пула при повторных попытках)
                current_impersonate = impersonate or self.config.default_impersonate
                if (
                    attempt.retry_state.attempt_number > 1
                    and self.config.auto_rotate_impersonate_on_retry
                    and self.config.impersonate_pool
                ):
                    pool = self.config.impersonate_pool
                    idx = (attempt.retry_state.attempt_number - 1) % len(pool)
                    current_impersonate = pool[idx]

                # Получаем сохраненные куки для домена
                stored_cookies = await self.cookie_storage.get_cookies(domain)

                try:
                    async with self.create_session(
                        proxy=current_proxy,
                        impersonate=current_impersonate,
                        custom_headers=headers,
                    ) as session:
                        # Устанавливаем куки в сессию
                        if stored_cookies:
                            session.cookies.update(stored_cookies)

                        response = await session.request(
                            method=method,  # type: ignore[arg-type]
                            url=url,
                            params=params,
                            data=data,
                            json=json,
                            **kwargs,
                        )

                        # Сохраняем новые куки из ответа
                        if response.cookies:
                            new_cookies = dict(response.cookies)
                            if new_cookies:
                                await self.cookie_storage.set_cookies(domain, new_cookies)

                        # Проверяем антифрод / ошибки статуса
                        if response.status_code in retry_cfg.retry_status_codes:
                            if self.proxy_manager and current_proxy:
                                self.proxy_manager.report_fail(current_proxy)
                            raise ScraperRequestError(
                                f"Received retryable status code {response.status_code} for {url}",
                                status_code=response.status_code,
                                url=url,
                            )

                        # Фиксируем успех прокси
                        if self.proxy_manager and current_proxy:
                            self.proxy_manager.report_success(current_proxy)

                        return response

                except Exception as exc:
                    if self.proxy_manager and current_proxy:
                        self.proxy_manager.report_fail(current_proxy)
                    if isinstance(exc, ScraperRequestError):
                        raise
                    raise ScraperRequestError(
                        f"Network error during {method} {url}: {exc}", url=url
                    ) from exc

        raise ScraperRequestError(f"Max attempts exceeded for {url}")

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Response:
        return await self.request("POST", url, **kwargs)

    async def scrape(
        self,
        url: str,
        model_cls: type[T] | None = None,
        query: str | None = None,
        extractor: Callable[[str], dict[str, Any]] | None = None,
        strict: bool = False,
        **kwargs: Any,
    ) -> ScrapeResult[Any]:
        """Высокоуровневый метод: делает запрос, извлекает состояние и упаковывает
        в стандартизированный контейнер ScrapeResult.
        """
        start_time = time.perf_counter()
        response = await self.get(url, **kwargs)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        html = response.text
        extracted_state: dict[str, Any] | None = None

        # 1. Извлечение состояния
        if extractor is not None:
            extracted_state = extractor(html)
        else:
            # Автоопределение формата гидратации
            if "__NEXT_DATA__" in html:
                try:
                    extracted_state = extract_next_data(html)
                except Exception:
                    pass

            if extracted_state is None and ("RelayPrefetchedStreamCache" in html or "data-sjs" in html):
                try:
                    relay_cache = extract_relay_cache(html)
                    if relay_cache:
                        extracted_state = relay_cache
                except Exception:
                    pass

            if extracted_state is None and "__NUXT_DATA__" in html:
                try:
                    nuxt_data = extract_nuxt_data(html)
                    if isinstance(nuxt_data, dict):
                        extracted_state = nuxt_data
                    elif isinstance(nuxt_data, list):
                        extracted_state = {"nuxt": nuxt_data}
                except Exception:
                    pass

            if extracted_state is None:
                json_ld = extract_json_ld(html)
                if json_ld:
                    extracted_state = {"json_ld": json_ld}

        # 2. Маппинг в Pydantic v2 модели
        items: list[Any] = []
        if extracted_state is not None and model_cls is not None and query is not None:
            mapped = map_state_to_model(
                state=extracted_state,
                query=query,
                model_cls=model_cls,
                strict=strict,
            )
            if isinstance(mapped, list):
                items = mapped
            elif mapped is not None:
                items = [mapped]

        impersonate_used = kwargs.get("impersonate", self.config.default_impersonate)
        proxy_used = kwargs.get("proxy", self.proxy_manager.get_proxy() if self.proxy_manager else None)

        return ScrapeResult(
            url=url,
            status_code=response.status_code,
            response_time_ms=duration_ms,
            impersonate_used=impersonate_used,
            proxy_used=proxy_used,
            items=items,
            state=extracted_state,
        )
