"""Пример 5: Сохранение результатов парсинга в PostgreSQL через SQLAlchemy 2.0 AsyncSession (UPSERT).

Демонстрирует атомарный UPSERT пачки записей: если товар уже есть в БД - обновляет цену,
если нет - вставляет новую запись без дубликатов.
"""

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from oniscrape import ScraperClient

# Для запуска в продакшене требуется: pip install sqlalchemy asyncpg
try:
    from sqlalchemy import Column, DateTime, Numeric, String, func  # type: ignore[import-not-found]
    from sqlalchemy.dialects.postgresql import insert  # type: ignore[import-not-found]
    from sqlalchemy.orm import DeclarativeBase  # type: ignore[import-not-found]

    class Base(DeclarativeBase):  # type: ignore[misc,valid-type]
        pass

    class ProductDBModel(Base):
        __tablename__ = "scraped_products"

        id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        price_usd = Column(Numeric(10, 2), nullable=True)
        updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    insert = None  # type: ignore[assignment]
    func = None  # type: ignore[assignment]
    ProductDBModel = None  # type: ignore[assignment,misc]


async def upsert_products(session: Any, items: list[BaseModel]) -> None:
    """Атомарный пакетный UPSERT в PostgreSQL."""
    if not HAS_SQLALCHEMY or insert is None or func is None or ProductDBModel is None:
        print("SQLAlchemy/asyncpg не установлены. Установите: pip install sqlalchemy asyncpg")
        return

    if not items:
        return

    raw_values = [item.model_dump() for item in items]
    stmt = insert(ProductDBModel).values(raw_values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[ProductDBModel.id],
        set_={
            "name": stmt.excluded.name,
            "price_usd": stmt.excluded.price_usd,
            "updated_at": func.now(),
        },
    )
    await session.execute(stmt)
    await session.commit()
    print(f"Успешно сохранен/обновлен пакет из {len(items)} товаров в PostgreSQL.")


class ProductSchema(BaseModel):
    id: str
    name: str
    price_usd: float = Field(alias="priceUsd")


async def main():
    # 1. Скрапинг данных через oniscrape
    async with ScraperClient() as client:
        result = await client.scrape(
            url="https://coinmarketcap.com/",
            model_cls=ProductSchema,
            query="props.pageProps.items[*].{id: id, name: name, priceUsd: price}",
            strict=False,
        )
        print(f"Спарсено записей: {result.items_count}")


if __name__ == "__main__":
    asyncio.run(main())
