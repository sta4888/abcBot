from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Создаёт async engine на основе настроек."""
    return create_async_engine(
        settings.postgres.dsn,
        echo=settings.debug,  # в dev выводит все SQL-запросы в лог
        pool_pre_ping=True,  # проверяет, что соединение живое, перед использованием
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Создаёт фабрику асинхронных сессий.

    Фабрика — вызываемый объект: session_factory() возвращает новую сессию.
    """
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,  # объекты не теряют атрибуты после commit
        class_=AsyncSession,
    )
