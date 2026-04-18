def test_python_works() -> None:
    """Базовый sanity check: Python вообще выполняет код."""
    assert 1 + 1 == 2


def test_imports_work() -> None:
    """Проверяем, что ключевые зависимости импортируются."""
    import aiogram  # noqa: F401
    import pydantic_settings  # noqa: F401


def test_settings_class_structure() -> None:
    """Settings должен иметь ожидаемые вложенные конфиги."""
    from bot.config import BotConfig, PostgresConfig, RedisConfig, Settings

    assert "token" in BotConfig.model_fields
    assert "host" in PostgresConfig.model_fields
    assert "port" in PostgresConfig.model_fields
    assert "host" in RedisConfig.model_fields
    assert "bot" in Settings.model_fields
    assert "postgres" in Settings.model_fields
    assert "redis" in Settings.model_fields


def test_db_modules_import() -> None:
    """Проверяем, что модули БД и модели импортируются."""
    from bot.db.base import Base  # noqa: F401
    from bot.db.engine import create_engine, create_session_factory  # noqa: F401
    from bot.db.session import get_session_factory  # noqa: F401
    from bot.models import User  # noqa: F401
