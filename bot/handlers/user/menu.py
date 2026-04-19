import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.user.main_menu import BTN_CART, BTN_HELP, BTN_ORDERS

logger = logging.getLogger(__name__)

router = Router(name="user.menu")


@router.message(F.text == BTN_CART)
async def on_cart_click(message: Message) -> None:
    """Нажатие 'Корзина' — заглушка."""
    logger.info("User %s clicked Cart", message.from_user.id if message.from_user else "?")
    await message.answer("Твоя корзина пока пуста. Загляни в каталог 🛍")


@router.message(F.text == BTN_ORDERS)
async def on_orders_click(message: Message) -> None:
    """Нажатие 'Мои заказы' — заглушка."""
    logger.info("User %s clicked Orders", message.from_user.id if message.from_user else "?")
    await message.answer("У тебя пока нет заказов.")


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
