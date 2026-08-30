from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProxyConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    urls: list[str] = Field(
        default_factory=list, description="Список URL прокси (socks5://..., http://...)"
    )
    cooldown_seconds: float = Field(
        default=120.0, ge=0.0, description="Время кулдауна заблокированного прокси"
    )
    max_fails_before_cooldown: int = Field(
        default=2, ge=1, description="Количество сбоев до отправки в кулдаун"
    )
    strategy: Literal["round_robin", "random", "least_failed"] = Field(
        default="round_robin", description="Стратегия выбора прокси"
    )


class RetryConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_attempts: int = Field(default=3, ge=1, description="Максимальное количество попыток")
    min_backoff_seconds: float = Field(
        default=0.5, ge=0.0, description="Минимальная пауза между попытками"
    )
    max_backoff_seconds: float = Field(default=5.0, ge=0.0, description="Максимальная пауза")
    retry_status_codes: set[int] = Field(
        default_factory=lambda: {403, 429, 500, 502, 503, 504},
        description="HTTP-статусы, требующие повторного запроса",
    )


class ScraperConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    default_impersonate: str = Field(
        default="chrome124", description="Дефолтный профиль TLS-фингерпринта в curl_cffi"
    )
    impersonate_pool: list[str] = Field(
        default_factory=lambda: ["chrome124", "chrome120", "safari17_0", "edge122"],
        description="Пул TLS-фингерпринтов для ротации при ретраях",
    )
    auto_rotate_impersonate_on_retry: bool = Field(
        default=True,
        description="Автоматически переключать TLS-фингерпринт при повторных попытках",
    )
    timeout_seconds: float = Field(default=30.0, ge=1.0, description="Таймаут сетевых запросов")
    verify_ssl: bool = Field(default=True, description="Проверка SSL-сертификатов")
    proxy: ProxyConfig = Field(default_factory=ProxyConfig, description="Настройки пула прокси")
    retry: RetryConfig = Field(default_factory=RetryConfig, description="Настройки ретраев")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Кастомные дефолтные заголовки"
    )
