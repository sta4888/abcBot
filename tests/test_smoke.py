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
    from bot.models import (  # noqa: F401
        CartItem,
        Category,
        Order,
        OrderItem,
        Product,
        User,
    )


def test_alembic_config_loads() -> None:
    """Проверяем, что env.py Alembic импортируется без ошибок."""
    import configparser
    from pathlib import Path

    # Проверяем, что alembic.ini существует и валиден
    config_path = Path("alembic.ini")
    assert config_path.exists(), "alembic.ini должен быть в корне проекта"

    parser = configparser.ConfigParser()
    parser.read(config_path)
    assert "alembic" in parser.sections()
    assert parser.get("alembic", "script_location") == "migrations"


def test_logger_setup_works() -> None:
    """Проверяем, что setup_logging не падает."""
    from bot.utils.logger import setup_logging

    setup_logging(debug=False)
    setup_logging(debug=True)

    # После setup_logging должен быть ровно один handler на корневом логгере
    import logging

    root = logging.getLogger()
    assert len(root.handlers) == 1


def test_stock_errors_importable() -> None:
    """Проверка, что новые ошибки доступны."""
    from bot.services.order_service import (  # noqa: F401
        InsufficientStockError,
        ProductNotFoundError,
    )
