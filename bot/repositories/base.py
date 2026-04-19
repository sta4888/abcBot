from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.base import Base


class BaseRepository[ModelT: Base]:
    """Общий родитель с параметризованным типом модели.

    Подкласс обязан задать model_cls — тип сущности, с которой работает.
    Пример: class UserRepository(BaseRepository[User]): model_cls = User
    """

    model_cls: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """Общая реализация get_by_id — через первичный ключ."""
        stmt = select(self.model_cls).where(self.model_cls.id == entity_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
