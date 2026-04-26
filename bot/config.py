from functools import cached_property, lru_cache

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseModel):
    """Настройки самого Telegram-бота."""

    token: SecretStr


class PostgresConfig(BaseModel):
    """Настройки подключения к PostgreSQL."""

    host: str
    port: int = 5432
    user: str
    password: SecretStr
    db: str

    @cached_property
    def dsn(self) -> str:
        """Строка подключения для asyncpg-драйвера SQLAlchemy."""
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"


class RedisConfig(BaseModel):
    """Настройки подключения к Redis."""

    host: str
    port: int = 6379
    db: int = 0

    @cached_property
    def dsn(self) -> str:
        """URL подключения к Redis."""
        return f"redis://{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    """Корневой объект настроек."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_nested_max_split=1,
        extra="ignore",
    )

    bot: BotConfig
    postgres: PostgresConfig
    redis: RedisConfig

    debug: bool = False
    sql_echo: bool = False
    product_placeholder_file_id: str = ""
    yookassa_enabled: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает singleton-инстанс настроек.

    Ленивая инициализация: Settings() вызывается только при первом обращении,
    что даёт возможность импортировать модуль без .env (например, в тестах).
    """
    return Settings()  # type: ignore[call-arg]
