import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.user.main_menu import get_main_menu
from bot.models import User

logger = logging.getLogger(__name__)

router = Router(name="user.start")


@router.message(CommandStart())
async def start_handler(message: Message, current_user: User) -> None:
    """Обрабатывает /start: показывает приветствие и меню.

    Регистрация пользователя теперь в AuthMiddleware, поэтому
    current_user уже есть к моменту входа в этот хендлер.
    """
    if message.from_user is None:
        return

    # Простое приветствие. Различение «новый/возвращающийся» уберём:
    # AuthMiddleware всегда подтягивает User, и мы не знаем, был ли он новый.
    # Это сознательное упрощение: «новый/старый» — это бизнес-логика,
    # которую можно было бы перенести в Observer на событие 'user.registered'.
    greeting = f"Привет, <b>{message.from_user.first_name or 'друг'}</b>!\nЭто бот-магазин. Выбери, с чего начнём."

    await message.answer(greeting, reply_markup=get_main_menu())


@router.message()
async def fallback_handler(message: Message) -> None:
    """Ловит всё, что не подошло ни одному другому хендлеру."""
    logger.info(
        "Fallback for user %s: %r",
        message.from_user.id if message.from_user else "?",
        message.text,
    )
    await message.answer("Не понял тебя 🤔 Нажми кнопку меню или /start")
