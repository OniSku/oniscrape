"""Пример 8: Скрапинг закрытых страниц с авторизацией через куки сессии (Session Injection).

Позволяет читать посты и данные, доступные только зарегистрированным пользователям,
без прохождения интерактивного логина и риска блокировки аккаунта.
"""

import asyncio

from oniscrape import ScraperClient, ScraperConfig


async def main():
    # 1. Вариант А: Загрузка куки напрямую из экспорта браузера (Cookie-Editor / JSON)
    # cookies = load_cookies_from_file("my_threads_cookies.json")
    # async with ScraperClient.from_cookies(cookies, domain="threads.net") as client:
    #     response = await client.get("https://www.threads.net/")
    #     print("Авторизованный ответ получен, размер:", len(response.text))

    # 2. Вариант Б: Передача строки Cookie в заголовках конфига
    config = ScraperConfig(
        default_impersonate="chrome124",
        headers={
            # Пример куки сессии
            "Cookie": "sessionid=test_mock_session; ds_user_id=12345;",
        },
    )

    async with ScraperClient(config=config) as client:
        print("Отправка запроса с сессионными куки...")
        response = await client.get("https://news.ycombinator.com/")
        print("Статус ответа:", response.status_code)


if __name__ == "__main__":
    asyncio.run(main())
