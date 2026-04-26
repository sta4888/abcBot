import logging
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CommandError(Exception):
    """Базовая ошибка выполнения команды."""


class Command(ABC):
    """Абстрактный Command.

    Конкретная команда:
    1. В __init__ принимает данные (order_id, user_id, ...)
    2. Перед execute()/undo() — bind_session(session) для привязки БД
    3. В execute() выполняет действие, сохраняет контекст для undo
    4. В undo() откатывает действие
    """

    def __init__(self) -> None:
        self.executed_at: datetime | None = None
        self.executor_user_id: int | None = None
        self.summary: str = ""
        self._session: AsyncSession | None = None

    def bind_session(self, session: AsyncSession) -> None:
        """Привязать свежую сессию перед execute() / undo().

        Команды переживают между апдейтами в History, исходная сессия
        к моменту undo уже закрыта. bind_session обновляет ссылку.
        """
        self._session = session

    def _require_session(self) -> AsyncSession:
        """Безопасный доступ к сессии. Кидает если не привязана."""
        if self._session is None:
            raise CommandError("Session not bound. Call bind_session(session) first.")
        return self._session

    @abstractmethod
    async def execute(self) -> bool:
        """Выполняет действие. True при успехе."""

    @abstractmethod
    async def undo(self) -> bool:
        """Откатывает действие. True при успехе."""
