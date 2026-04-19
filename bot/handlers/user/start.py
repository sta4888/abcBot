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
            f"С возвращением, <b>{message.from_user.first_name or 'друг'}</b>!\nЧем займёмся?"
        )

    await message.answer(greeting, reply_markup=get_main_menu())


@router.message()
async def fallback_handler(message: Message) -> None:
    """Ловит всё, что не подошло ни одному другому хендлеру.

    Важно: должен быть зарегистрирован ПОСЛЕ всех остальных хендлеров-роутеров.
    Поэтому фолбэк не в menu.py, а в start.py, и start-роутер подключается последним.
    """
    logger.info(
        "Fallback for user %s: %r",
        message.from_user.id if message.from_user else "?",
        message.text,
    )
    await message.answer("Не понял тебя 🤔 Нажми кнопку меню или /start")
