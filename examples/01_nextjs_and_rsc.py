"""Пример 1: Парсинг Next.js SSR (__NEXT_DATA__) и React Server Components (RSC Flight stream)."""

import asyncio

from pydantic import BaseModel, Field

from oniscrape import (
    ScraperClient,
    extract_next_data,
    extract_rsc_flight,
)


class CryptoListing(BaseModel):
    name: str = Field(description="Название монеты")
    symbol: str = Field(description="Тикер")


async def main():
    async with ScraperClient() as client:
        # --- 1. Извлечение классического __NEXT_DATA__ ---
        print("1. Запрос к сайту на базе Next.js Pages Router...")
        response = await client.get("https://coinmarketcap.com/")

        state = extract_next_data(response.text)
        print(f" -> Успешно извлечено состояние гидратации: {len(state.get('props', {}))} ключей в props")

        # --- 2. Извлечение React 19 / App Router RSC Flight stream ---
        print("\n2. Запрос к сайту на базе Next.js App Router (RSC)...")
        rsc_response = await client.get("https://nextjs.org/")

        flight_tree = extract_rsc_flight(rsc_response.text)
        print(f" -> Успешно декодировано {len(flight_tree)} слотов состояния React Server Components!")


if __name__ == "__main__":
    asyncio.run(main())
