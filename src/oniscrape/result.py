from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

import orjson
from pydantic import BaseModel

T = TypeVar("T")


@dataclass
class ScrapeResult(Generic[T]):
    """Стандартизированный контейнер результатов скрапинга с метаданными запроса
    и встроенными методами экспорта и сохранения.
    """

    url: str
    status_code: int
    response_time_ms: float = 0.0
    impersonate_used: str = "chrome124"
    proxy_used: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    items: list[T] = field(default_factory=list)
    state: dict[str, Any] | None = None

    @property
    def items_count(self) -> int:
        return len(self.items)

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def _serialize_items(self) -> list[Any]:
        serialized: list[Any] = []
        for item in self.items:
            if isinstance(item, BaseModel):
                serialized.append(item.model_dump())
            elif isinstance(item, dict):
                serialized.append(item)
            else:
                serialized.append(item)
        return serialized

    def to_dict(self) -> dict[str, Any]:
        """Возвращает чистый структурированный словарь без сырого HTML."""
        return {
            "url": self.url,
            "status_code": self.status_code,
            "response_time_ms": round(self.response_time_ms, 2),
            "impersonate_used": self.impersonate_used,
            "proxy_used": self.proxy_used,
            "timestamp": self.timestamp,
            "items_count": self.items_count,
            "items": self._serialize_items(),
        }

    def to_json(self, indent: bool = False) -> str:
        """Сериализует результат в JSON-строку с помощью высокоскоростного Rust-парсера orjson."""
        option = orjson.OPT_INDENT_2 if indent else None
        return orjson.dumps(self.to_dict(), option=option).decode("utf-8")

    def save_json(self, filepath: str | Path, indent: bool = True) -> None:
        """Сохраняет структурированный результат в JSON-файл."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        option = orjson.OPT_INDENT_2 if indent else None
        data_bytes = orjson.dumps(self.to_dict(), option=option)
        path.write_bytes(data_bytes)

    def append_ndjson(self, filepath: str | Path) -> None:
        """Потоковая дозапись валидированных элементов в NDJSON (JSON Lines) файл."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as f:
            for item in self.items:
                raw = item.model_dump() if isinstance(item, BaseModel) else item
                f.write(orjson.dumps(raw))
                f.write(b"\n")

    def to_polars(self) -> Any:
        """Экспорт списка извлеченных элементов в Polars DataFrame (требуется библиотека polars)."""
        try:
            import polars as pl  # type: ignore[import-not-found,import-untyped]
        except ImportError as err:
            raise ImportError(
                "Библиотека polars не установлена. Установите ее через: pip install polars"
            ) from err

        data = self._serialize_items()
        return pl.DataFrame(data)
