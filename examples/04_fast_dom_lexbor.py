"""Пример 4: Быстрый C-уровень DOM-парсинга через Selectolax Lexbor."""

import asyncio

from oniscrape import (
    ScraperClient,
    css_all_attr,
    css_all_text,
    parse_html,
)


async def main():
    async with ScraperClient() as client:
        print("Запрос к Hacker News...")
        response = await client.get("https://news.ycombinator.com/")

        # Парсинг на Си-движке Lexbor
        tree = parse_html(response.text)
        titles = css_all_text(tree, ".titleline > a")
        links = css_all_attr(tree, ".titleline > a", "href")

        print(f"Успешно извлечено {len(titles)} записей:")
        for idx, (title, url) in enumerate(zip(titles[:5], links[:5], strict=False), 1):
            print(f" {idx}. {title} -> {url}")


if __name__ == "__main__":
    asyncio.run(main())
