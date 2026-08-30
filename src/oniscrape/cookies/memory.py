import asyncio
from typing import Any

from .base import BaseCookieStorage


class InMemoryCookieStorage(BaseCookieStorage):
    """Потокобезопасное хранилище куки в оперативной памяти."""

    def __init__(self, initial_cookies: dict[str, Any] | None = None):
        self._cookies: dict[str, dict[str, str]] = {}
        if initial_cookies:
            # Если передан плоский словарь куки {"sessionid": "..."}
            if all(isinstance(v, str) for v in initial_cookies.values()):
                self._cookies[""] = initial_cookies.copy()
            else:
                for dom, cookies_dict in initial_cookies.items():
                    if isinstance(cookies_dict, dict):
                        self._cookies[str(dom)] = cookies_dict.copy()
        self._lock = asyncio.Lock()

    async def get_cookies(self, domain: str) -> dict[str, str]:
        async with self._lock:
            # Возвращаем общие куки (пустой домен) + куки домена
            merged = self._cookies.get("", {}).copy()
            if domain and domain in self._cookies:
                merged.update(self._cookies[domain])
            return merged

    async def set_cookies(self, domain: str, cookies: dict[str, str]) -> None:
        async with self._lock:
            if domain not in self._cookies:
                self._cookies[domain] = {}
            self._cookies[domain].update(cookies)

    async def clear(self, domain: str | None = None) -> None:
        async with self._lock:
            if domain:
                self._cookies.pop(domain, None)
            else:
                self._cookies.clear()
