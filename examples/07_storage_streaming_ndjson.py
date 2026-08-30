"""Пример 7: Потоковая дозапись результатов скрапинга в файл NDJSON (JSON Lines).

Позволяет сохранять результаты непрерывного скрапинга без накопления в оперативной памяти.
"""

import asyncio
from pathlib import Path

from pydantic import BaseModel, Field

from oniscrape import ScraperClient


class NewsItem(BaseModel):
    title: str
    url: str = Field(alias="link")


async def main():
    ndjson_file = Path("scraped_news_stream.ndjson")

    async with ScraperClient() as client:
        print("Запуск скрапинга и потокового сохранения...")
        response = await client.get("https://news.ycombinator.com/")

        from oniscrape import css_all_attr, css_all_text, parse_html

        tree = parse_html(response.text)
        titles = css_all_text(tree, ".titleline > a")
        links = css_all_attr(tree, ".titleline > a", "href")

        items = [
            NewsItem(title=title_text, link=link_url)
            for title_text, link_url in zip(titles[:10], links[:10], strict=False)
        ]

        from oniscrape.result import ScrapeResult

        res = ScrapeResult(
            url="https://news.ycombinator.com/",
            status_code=response.status_code,
            items=items,
        )

        # 1. Потоковая дозапись в NDJSON
        res.append_ndjson(ndjson_file)
        print(f"Успешно дозаписано {res.items_count} записей в {ndjson_file}")

        # 2. Сохранение в структурированный JSON
        res.save_json("scraped_news_clean.json", indent=True)
        print("Сохранен чистый JSON в scraped_news_clean.json")


if __name__ == "__main__":
    asyncio.run(main())
