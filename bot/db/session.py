from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import get_settings
from bot.db.engine import create_engine, create_session_factory


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Возвращает фабрику сессий (создаётся один раз на процесс)."""
    settings = get_settings()
    engine = create_engine(settings)
    return create_session_factory(engine)
