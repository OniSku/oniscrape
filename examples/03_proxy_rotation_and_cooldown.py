"""Пример 3: Настройка пула прокси (SOCKS5/HTTP, Cloudflare WARP) с авто-ротацией и кулдауном."""

import asyncio

from oniscrape import (
    ProxyConfig,
    ScraperClient,
    ScraperConfig,
)


async def main():
    # Конфигурация пула с авто-кулдауном заблокированных прокси
    config = ScraperConfig(
        default_impersonate="chrome124",
        timeout_seconds=10.0,
        proxy=ProxyConfig(
            urls=[
                "socks5://127.0.0.1:40000", # Пример: локальный Cloudflare WARP SOCKS5
                "socks5://127.0.0.1:40001",
            ],
            strategy="least_failed", # или "round_robin", "random"
            cooldown_seconds=60.0,   # Время блокировки прокси при получении 403/429
            max_fails_before_cooldown=2,
        ),
    )

    print("Инициализация клиента с пулом прокси...")
    async with ScraperClient(config=config) as client:
        # Сессии изолируются под каждый прокси - исключая залипание Keep-Alive сокетов
        print(f"Всего прокси в пуле: {client.proxy_manager.total_count if client.proxy_manager else 0}")


if __name__ == "__main__":
    asyncio.run(main())
