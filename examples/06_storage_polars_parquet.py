"""Пример 6: Сохранение результатов парсинга в Apache Parquet (ZSTD) через Polars.

Идеально подходит для аналитики, датасетов и больших объемов данных (сжатие до 80%).
"""

import asyncio

from pydantic import BaseModel

from oniscrape import ScraperClient


class CryptoItem(BaseModel):
    id: int
    name: str
    symbol: str


async def main():
    async with ScraperClient() as client:
        # Получаем данные
        result = await client.scrape(
            url="https://coinmarketcap.com/",
            query="props.dehydratedState.queries[?queryKey[0]=='global-metric'].state.data | [0]",
        )
        print(f"Статус ответа: {result.status_code}, время: {result.response_time_ms} ms")

        # Сохранение через result.to_polars()
        # df = result.to_polars()
        # df.write_parquet("cryptos.parquet", compression="zstd")
        # print("Сохранено в cryptos.parquet")


if __name__ == "__main__":
    asyncio.run(main())
