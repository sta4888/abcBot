from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Общий родитель: каждый репозиторий работает в рамках одной сессии."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
