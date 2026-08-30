from typing import Any

import orjson

from .base import BaseCookieStorage


class RedisCookieStorage(BaseCookieStorage):
    """Распределенное асинхронное хранилище куки в Redis."""

    def __init__(self, redis_client: Any, prefix: str = "oniscrape:cookies:"):
        self.redis = redis_client
        self.prefix = prefix

    def _key(self, domain: str) -> str:
        return f"{self.prefix}{domain}"

    async def get_cookies(self, domain: str) -> dict[str, str]:
        raw = await self.redis.get(self._key(domain))
        if not raw:
            return {}
        try:
            return orjson.loads(raw)
        except Exception:
            return {}

    async def set_cookies(self, domain: str, cookies: dict[str, str]) -> None:
        current = await self.get_cookies(domain)
        current.update(cookies)
        await self.redis.set(self._key(domain), orjson.dumps(current))

    async def clear(self, domain: str | None = None) -> None:
        if domain:
            await self.redis.delete(self._key(domain))
        else:
            # Поиск всех ключей с префиксом через SCAN
            async for key in self.redis.scan_iter(match=f"{self.prefix}*"):
                await self.redis.delete(key)
