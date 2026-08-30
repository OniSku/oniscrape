import random
import threading
from typing import Literal

from ..config import ProxyConfig
from .health import ProxyState


class ProxyManager:
    """Потокобезопасный менеджер пула прокси с поддержкой стратегий и кулдауна."""

    def __init__(self, config: ProxyConfig):
        self.config = config
        self._lock = threading.Lock()
        self._states: dict[str, ProxyState] = {url: ProxyState(url=url) for url in config.urls}
        self._index = 0

    @property
    def total_count(self) -> int:
        return len(self._states)

    def add_proxy(self, url: str) -> None:
        with self._lock:
            if url not in self._states:
                self._states[url] = ProxyState(url=url)

    def remove_proxy(self, url: str) -> None:
        with self._lock:
            self._states.pop(url, None)

    def get_proxy(
        self, strategy: Literal["round_robin", "random", "least_failed"] | None = None
    ) -> str | None:
        """Возвращает живой прокси по заданной стратегии или None, если пул пуст."""
        with self._lock:
            if not self._states:
                return None

            available = [state for state in self._states.values() if state.is_available()]
            if not available:
                # Если все в кулдауне, берем тот, у которого быстрее всего закончится кулдаун
                available = sorted(self._states.values(), key=lambda s: s.cooldown_until)

            strat = strategy or self.config.strategy

            if strat == "random":
                return random.choice(available).url

            if strat == "least_failed":
                # Сортируем по числу ошибок
                sorted_by_fails = sorted(available, key=lambda s: (s.fail_count, -s.success_count))
                return sorted_by_fails[0].url

            # Round-Robin по умолчанию
            self._index = (self._index + 1) % len(available)
            return available[self._index].url

    def report_success(self, url: str) -> None:
        with self._lock:
            if url in self._states:
                self._states[url].mark_success()

    def report_fail(self, url: str) -> None:
        with self._lock:
            if url in self._states:
                self._states[url].mark_fail(
                    max_fails=self.config.max_fails_before_cooldown,
                    cooldown_seconds=self.config.cooldown_seconds,
                )
