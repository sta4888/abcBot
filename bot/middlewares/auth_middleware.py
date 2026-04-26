import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Загружает User из БД (или создаёт, если впервые) на каждый апдейт.

    Зависит от DatabaseMiddleware: ожидает session в data.
    Подключать в dispatcher ПОСЛЕ DatabaseMiddleware.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = self._extract_from_user(event)
        if from_user is None:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        user_repo = UserRepository(session)
        user, _ = await user_repo.get_or_create(
            user_id=from_user.id,
            username=from_user.username,
            first_name=from_user.first_name,
            last_name=from_user.last_name,
        )
        data["current_user"] = user

        return await handler(event, data)

    @staticmethod
    def _extract_from_user(event: TelegramObject) -> Any:
        """Универсально достаёт from_user из Message и CallbackQuery."""
        if isinstance(event, Message | CallbackQuery):
            return event.from_user
        return None
