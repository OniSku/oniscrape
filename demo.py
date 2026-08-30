import asyncio

from pydantic import BaseModel, Field

from oniscrape import (
    ScraperClient,
    css_all_attr,
    css_all_text,
    extract_next_data,
    extract_rsc_flight,
    find_rsc_payload,
    map_state_to_model,
    parse_html,
)


# --- Схемы данных Pydantic v2 ---
class CryptoMetric(BaseModel):
    num_cryptos: int = Field(alias="numCryptocurrencies", description="Всего криптовалют в мире")
    num_markets: int = Field(alias="numMarkets", description="Количество активных рынков")
    active_exchanges: int = Field(alias="activeExchanges", description="Активных бирж")


class HackerNewsItem(BaseModel):
    title: str
    link: str


async def demo_live_scrape_result_pipeline():
    print("\n--- [1] РЕАЛЬНЫЙ ЗАПРОС: High-Level client.scrape() -> ScrapeResult ---")
    print("Автоматический пайплайн: HTTP/2 запрос + извлечение + валидация + упаковка в ScrapeResult...")

    async with ScraperClient() as client:
        result = await client.scrape(
            url="https://coinmarketcap.com/",
            model_cls=CryptoMetric,
            query="props.dehydratedState.queries[?queryKey[0]=='global-metric'].state.data | [0]",
            strict=False,
        )

        print(f"Статус: {result.status_code}, Время: {result.response_time_ms:.2f} ms")
        print(f"Использованный TLS: {result.impersonate_used}")
        print("Чистый словарь результата (result.to_dict()):")
        print(f" -> {result.to_dict()}")

        # Сохранение чистого результата без HTML в JSON
        result.save_json("sample_scrape_result.json", indent=True)
        print("Результат сохранен в sample_scrape_result.json")


async def demo_live_nextjs_state():
    print("\n--- [2] РЕАЛЬНЫЙ ЗАПРОС: Next.js SSR гидратация (CoinMarketCap) ---")

    async with ScraperClient() as client:
        response = await client.get("https://coinmarketcap.com/")
        state = extract_next_data(response.text)
        metrics = map_state_to_model(
            state=state,
            query="props.dehydratedState.queries[?queryKey[0]=='global-metric'].state.data | [0]",
            model_cls=CryptoMetric,
            strict=False,
        )

        if isinstance(metrics, CryptoMetric):
            print("Извлеченные данные:")
            print(f" -> Всего криптовалют: {metrics.num_cryptos:,}")
            print(f" -> Активных рынков: {metrics.num_markets:,}")


async def demo_live_rsc_flight():
    print("\n--- [3] РЕАЛЬНЫЙ ЗАПРОС: React Server Components (Nextjs.org App Router) ---")

    async with ScraperClient() as client:
        response = await client.get("https://nextjs.org/")
        flight_tree = extract_rsc_flight(response.text)
        print(f"Успешно декодировано {len(flight_tree)} слотов состояния RSC!")

        # Поиск полезных объектов в RSC дереве
        sample_payloads = find_rsc_payload(flight_tree)
        print(f"Найдено полезных блоков данных через find_rsc_payload: {len(sample_payloads) if isinstance(sample_payloads, list) else 1}")


async def demo_live_lexbor_dom():
    print("\n--- [4] РЕАЛЬНЫЙ ЗАПРОС: DOM-парсинг Hacker News через Selectolax Lexbor ---")

    async with ScraperClient() as client:
        response = await client.get("https://news.ycombinator.com/")
        tree = parse_html(response.text)
        titles = css_all_text(tree, ".titleline > a")
        links = css_all_attr(tree, ".titleline > a", "href")

        print(f"Извлечено {len(titles)} актуальных новостей:")
        for idx, (t, link) in enumerate(zip(titles[:3], links[:3], strict=False), 1):
            print(f" {idx}. {t}")
            print(f"    URL: {link}")


async def main():
    print("==================================================================")
    print("   РЕАЛЬНАЯ ДЕМОНСТРАЦИЯ ONISCRAPE v0.2.0: LIVE ПАРСИНГ          ")
    print("==================================================================")

    await demo_live_scrape_result_pipeline()
    await demo_live_nextjs_state()
    await demo_live_rsc_flight()
    await demo_live_lexbor_dom()

    print("\n==================================================================")
    print("   Все РЕАЛЬНЫЕ сетевые сценарии успешно выполнены!              ")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
