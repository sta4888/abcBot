import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Наши импорты — Settings и Base + модели
import bot.models  # noqa: F401 — импорт регистрирует все модели в Base.metadata
from bot.config import get_settings
from bot.db.base import Base

# Конфиг Alembic из alembic.ini
config = context.config

# Настраиваем логирование по [loggers]/[handlers] в alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подставляем DSN из наших настроек
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.postgres.dsn)

# target_metadata используется для автогенерации миграций
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Миграции в offline-режиме (без подключения к БД, выводят SQL в stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Синхронная функция, которая будет запущена внутри run_sync."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # отслеживать изменения типов колонок
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Миграции в online-режиме через async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Точка входа для online-режима: запускает async-миграции."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
