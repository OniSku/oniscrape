"""Пример 2: Извлечение Relay Cache и токенов Meta (Threads / Instagram)."""

import asyncio

from oniscrape import (
    ScraperClient,
    extract_meta_tokens,
    extract_relay_cache,
)


async def main():
    async with ScraperClient() as client:
        print("Запрос к Threads профилю/странице...")
        response = await client.get("https://www.threads.net/")

        # 1. Извлечение токенов для последующих прямых POST-запросов к /api/graphql
        tokens = extract_meta_tokens(response.text)
        print("Извлеченные токены Meta:")
        print(f" -> LSD Token: {tokens['lsd']}")
        print(f" -> App ID:    {tokens['app_id']}")

        # 2. Умный распаковщик Relay Cache
        unwrapped_cache = extract_relay_cache(response.text)
        print(f" -> Успешно распаковано {len(unwrapped_cache)} запросов из Relay Cache:")
        for query_name in list(unwrapped_cache.keys())[:3]:
            print(f"    - [{query_name}]")


if __name__ == "__main__":
    asyncio.run(main())
