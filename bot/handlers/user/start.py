import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user.main_menu import get_main_menu
from bot.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = Router(name="user.start")


@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession) -> None:
    """Обрабатывает /start: регистрирует пользователя (если новичок), показывает меню."""
    if message.from_user is None:
        # /start в канале или служебный апдейт — игнорируем
        return

    user_repo = UserRepository(session)
    _, is_created = await user_repo.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    if is_created:
        greeting = (
            f"Добро пожаловать, <b>{message.from_user.first_name or 'друг'}</b>!\n"
            f"Это бот-магазин. Выбери, с чего начнём."
        )
        logger.info("New user registered: id=%d", message.from_user.id)
    else:
        greeting = (
            f"С возвращением, <b>{message.from_user.first_name or 'друг'}</b>!\n" f"Чем займёмся?"
        )

    await message.answer(greeting, reply_markup=get_main_menu())
