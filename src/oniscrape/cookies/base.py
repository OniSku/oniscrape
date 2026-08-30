from abc import ABC, abstractmethod


class BaseCookieStorage(ABC):
    """Абстрактное хранилище куки для сессий скрапера."""

    @abstractmethod
    async def get_cookies(self, domain: str) -> dict[str, str]:
        """Получить словарь куки для указанного домена."""
        ...

    @abstractmethod
    async def set_cookies(self, domain: str, cookies: dict[str, str]) -> None:
        """Сохранить или обновить куки для домена."""
        ...

    @abstractmethod
    async def clear(self, domain: str | None = None) -> None:
        """Очистить куки для домена или все."""
        ...
