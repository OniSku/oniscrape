import time
from dataclasses import dataclass


@dataclass
class ProxyState:
    url: str
    fail_count: int = 0
    success_count: int = 0
    last_fail_time: float = 0.0
    last_success_time: float = 0.0
    is_in_cooldown: bool = False
    cooldown_until: float = 0.0

    def mark_success(self) -> None:
        self.success_count += 1
        self.fail_count = 0
        self.last_success_time = time.monotonic()
        self.is_in_cooldown = False
        self.cooldown_until = 0.0

    def mark_fail(self, max_fails: int, cooldown_seconds: float) -> None:
        self.fail_count += 1
        self.last_fail_time = time.monotonic()
        if self.fail_count >= max_fails:
            self.is_in_cooldown = True
            self.cooldown_until = time.monotonic() + cooldown_seconds

    def is_available(self) -> bool:
        if not self.is_in_cooldown:
            return True
        if time.monotonic() >= self.cooldown_until:
            # Кулдаун истек - восстанавливаем прокси
            self.is_in_cooldown = False
            self.fail_count = 0
            self.cooldown_until = 0.0
            return True
        return False
