from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from bot.models import User


class AdminFilter(BaseFilter):
    """Фильтр для роутеров: проходят только админы."""

    async def __call__(
        self,
        event: TelegramObject,
        current_user: User | None = None,
    ) -> bool:
        if current_user is None:
            return False
        return current_user.is_admin
