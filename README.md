# oniscrape 🚀

[![PyPI version](https://img.shields.io/pypi/v/oniscrape.svg)](https://pypi.org/project/oniscrape/)
[![Python versions](https://img.shields.io/pypi/pyversions/oniscrape.svg)](https://pypi.org/project/oniscrape/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-OniSku%2Foniscrape-blue.svg)](https://github.com/OniSku/oniscrape)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> **Высокопроизводительный асинхронный скрапинг-движок для Python на базе `curl_cffi` (TLS/JA3/JA4 spoofing), `selectolax` (C/Lexbor), `orjson` (Rust) и `Pydantic v2`.**

📂 **Исходный код и примеры:** [https://github.com/OniSku/oniscrape](https://github.com/OniSku/oniscrape)  
📁 **Папка с готовыми скриптами:** [https://github.com/OniSku/oniscrape/tree/main/examples](https://github.com/OniSku/oniscrape/tree/main/examples)

Специализированный фреймворк для сверхбыстрого сбора данных с современных веб-приложений (Next.js SSR, React Server Components, Threads/Instagram Relay Cache, Nuxt) и закрытых сайтов с авторизацией **без запуска тяжелых headless-браузеров**.

---

## ⚡ Почему не Playwright / Selenium?

| Параметр | Headless Браузер (Playwright / Puppeteer) | `oniscrape` (State & API Engine) |
| :--- | :--- | :--- |
| **Потребление RAM** | ~300 - 600 МБ на вкладку | **~15 - 30 МБ на процесс** |
| **Время ответа** | 3.0 - 8.0 секунд (DOM + JS) | **0.1 - 0.4 секунды** (чистый сетевой I/O) |
| **Устойчивость к редизайнам** | Низкая (CSS-классы меняются при каждом билде) | **Высокая** (структура State/API стабильна годами) |
| **Обход TLS-проверок** | Зависит от stealth-патчей Chromium | **Нативный JA3/JA4 / HTTP2 спуфинг через `curl_cffi`** |
| **Утечки IP при смене прокси** | Залипание сокетов в пуле браузера | **Гарантированная изоляция сокетов на уровне сессий** |
| **Скорость парсинга JSON** | Стандартный JSON (~медленно) | **Ядро на Rust (`orjson`) — в 10 раз быстрее** |

---

## 📦 Установка

```bash
pip install oniscrape
```

или через **`uv`**:
```bash
uv add oniscrape
```

Для распределенного кэша сессий в Redis:
```bash
pip install oniscrape[redis]
```

---

## 🎯 Быстрый старт: `client.scrape()` и `ScrapeResult`

Выполняет полный цикл скрапинга в 1 строчку: отправляет HTTP/2 запрос с TLS-спуфингом, автоматически определяет тип гидратации страницы, валидирует данные в Pydantic v2 и возвращает структурированный результат:

```python
import asyncio
from pydantic import BaseModel, Field
from oniscrape import ScraperClient

class CryptoItem(BaseModel):
    id: str
    title: str = Field(alias="name")
    price: float = Field(alias="cost")

async def main():
    async with ScraperClient() as client:
        # 1. Запрос + авто-экстракция + Pydantic-валидация
        result = await client.scrape(
            url="https://example-store.com/catalog",
            model_cls=CryptoItem,
            query="props.pageProps.items[*].{id: item_id, name: name, cost: price}",
            strict=False,
        )
        
        # 2. Чистые метаданные и метрики
        print(f"Статус: {result.status_code} | Время ответа: {result.response_time_ms} ms")
        print(f"Извлечено записей: {result.items_count}")
        
        # 3. Чистый словарь без HTML-мусора
        data = result.to_dict()
        
        # 4. Мгновенное сохранение в JSON / NDJSON / Polars
        result.save_json("output_clean.json", indent=True)
        result.append_ndjson("stream_data.ndjson")

asyncio.run(main())
```

---

## 🔐 Скрапинг закрытых сайтов с авторизацией (Session Injection)

Для сбора данных на сайтах, где контент скрыт за авторизацией (Threads, Instagram, закрытые каталоги, форумы), используется безопасная инъекция сессии. Это исключает ввод логинов/паролей ботом и предотвращает блокировку аккаунтов антифродом.

### Способ 1: Загрузка куки из файла браузера (Cookie-Editor / JSON / Netscape)
Экспортируйте куки авторизованного профиля через расширение (например, Cookie-Editor) в JSON или текстовый файл:

```python
import asyncio
from oniscrape import ScraperClient

async def main():
    # Загружает куки авторизации из файла в 1 строчку
    async with ScraperClient.from_cookies_file("my_account_cookies.json") as client:
        result = await client.scrape("https://www.threads.net/")
        print("Спарсено от имени аккаунта:", result.items_count)

asyncio.run(main())
```

### Способ 2: Передача сессионных куки через `ScraperConfig`

```python
from oniscrape import ScraperClient, ScraperConfig

config = ScraperConfig(
    headers={
        "Cookie": "sessionid=68192847291%3AjK829...; ds_user_id=12345678;",
    }
)

async with ScraperClient(config=config) as client:
    response = await client.get("https://closed-portal.com/feed")
```

---

## 🚀 Пошаговые рецепты

### 1. Парсинг Next.js SSR (`__NEXT_DATA__`)
Мгновенно извлекает состояние гидратации без CSS-селекторов:

```python
from oniscrape import ScraperClient, extract_next_data, map_state_to_model

async with ScraperClient() as client:
    resp = await client.get("https://coinmarketcap.com/")
    state = extract_next_data(resp.text)
    metrics = map_state_to_model(
        state=state,
        query="props.dehydratedState.queries[0].state.data",
        model_cls=MyModel,
    )
```

### 2. React Server Components (RSC Flight в Next.js 14 / 15 / 19)
Декодирует потоковый протокол `self.__next_f.push` и ищет пропсы:

```python
from oniscrape import ScraperClient, extract_rsc_flight, find_rsc_payload

async with ScraperClient() as client:
    resp = await client.get("https://nextjs.org/")
    flight_tree = extract_rsc_flight(resp.text)
    
    # Рекурсивный поиск нужного объекта данных по ключу
    products = find_rsc_payload(flight_tree, target_key="products")
```

### 3. Smart Relay Unwrapper (Threads / Instagram)
Автоматически распаковывает вложенные структуры `ScheduledServerJS -> __bbox` в плоский словарь:

```python
from oniscrape import ScraperClient, extract_relay_cache, extract_meta_tokens

async with ScraperClient() as client:
    resp = await client.get("https://www.threads.net/@zuck")
    
    tokens = extract_meta_tokens(resp.text)  # LSD Token, App ID для GraphQL
    cache = extract_relay_cache(resp.text)   # Словарь {QueryName: data}
```

### 4. C-уровень DOM-парсинга (Selectolax Lexbor)
В 20 раз быстрее BeautifulSoup для классического HTML:

```python
from oniscrape import ScraperClient, parse_html, css_all_text, css_all_attr

async with ScraperClient() as client:
    resp = await client.get("https://news.ycombinator.com/")
    tree = parse_html(resp.text)
    titles = css_all_text(tree, ".titleline > a")
    links = css_all_attr(tree, ".titleline > a", "href")
```

---

## 💾 Сохранение данных (Data Persistence 2026)

### 1. PostgreSQL AsyncSession (UPSERT)
Атомарное обновление каталогов без дубликатов через `on_conflict_do_update`:

```python
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

async def upsert_items(session: AsyncSession, model_cls, items: list[dict]):
    if not items:
        return
    stmt = insert(model_cls).values(items)
    stmt = stmt.on_conflict_do_update(
        index_elements=[model_cls.id],
        set_={"price": stmt.excluded.price, "updated_at": func.now()}
    )
    await session.execute(stmt)
    await session.commit()
```

### 2. Polars + Apache Parquet (ZSTD Сжатие)
Сжатие до 80%, сохранение типов колонок и мгновенное чтение:

```python
df = result.to_polars()
df.write_parquet("catalog.parquet", compression="zstd")
```

### 3. Потоковый NDJSON (JSON Lines)
Дозапись в файл без удержания массива в RAM:

```python
result.append_ndjson("stream_output.ndjson")
```

---

## ⚙️ Ротация прокси и TLS-отпечатков

```python
from oniscrape import ScraperClient, ScraperConfig, ProxyConfig, RetryConfig

config = ScraperConfig(
    default_impersonate="chrome124",
    # Авто-ротация TLS при ошибках 403 / 429
    impersonate_pool=["chrome124", "chrome120", "safari17_0", "edge122"],
    auto_rotate_impersonate_on_retry=True,
    
    proxy=ProxyConfig(
        urls=["socks5://127.0.0.1:40000", "http://user:pass@proxy.example.com:8080"],
        strategy="least_failed",     # "round_robin" | "random" | "least_failed"
        cooldown_seconds=120.0,      # Время отстоя при ошибках
    ),
    retry=RetryConfig(max_attempts=3, retry_status_codes={403, 429, 500, 502, 503, 504}),
)
```

---

## 🧪 Тестирование

```bash
uv run --with pytest --with pytest-asyncio pytest -v
uv run --with ruff ruff check src tests examples
uv run --with pyright --with pytest pyright src tests examples
```

---

## 📄 Лицензия

MIT License (c) 2026 Oniscrape Authors.
