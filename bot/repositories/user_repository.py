import logging

from sqlalchemy import select

from bot.models import User
from bot.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Работа с пользователями в БД."""

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по Telegram ID или None, если не найден."""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> User:
        """Создаёт нового пользователя. Commit делает вызывающая сторона."""
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self._session.add(user)
        await self._session.flush()  # чтобы сразу получить id/created_at от БД
        logger.info("Created new user: %r", user)
        return user

    async def get_or_create(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> tuple[User, bool]:
        """Находит пользователя или создаёт. Возвращает (user, is_created).

        Типичный Upsert для регистрации при первом /start.
        """
        user = await self.get_by_id(user_id)
        if user is not None:
            return user, False
        user = await self.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        return user, True
