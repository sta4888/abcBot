import logging

from aiogram import Router
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router(name="user.start")


@router.message()
async def echo_any_message(message: Message) -> None:
    """Временный echo-хендлер — отвечает копией любого текста.

    Будет заменён на реальные хендлеры /start, меню и т.п. в следующих этапах.
    """
    logger.info(
        "Got message from user_id=%s: %r",
        message.from_user.id if message.from_user else None,
        message.text,
    )
    if message.text:
        await message.answer(f"Echo: {message.text}")
    else:
        await message.answer("Я принимаю только текст (пока)")
