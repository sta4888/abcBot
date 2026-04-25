import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.user.main_menu import BTN_HELP

logger = logging.getLogger(__name__)

router = Router(name="user.menu")


@router.message(F.text == BTN_HELP)
async def on_help_click(message: Message) -> None:
    """Нажатие 'Помощь'."""
    await message.answer(
        "<b>Как пользоваться ботом</b>\n\n"
        "• Нажми «Каталог», чтобы посмотреть товары\n"
        "• Добавляй понравившиеся в корзину\n"
        "• Оформляй заказ, когда будешь готов\n"
        "• В «Мои заказы» следи за статусом покупок\n\n"
        "Если что-то не работает — напиши /start, это всегда возвращает в меню."
    )
