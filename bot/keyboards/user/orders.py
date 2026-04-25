from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import OrderPayCallback


class OrdersKeyboardFactory:
    """Фабрика клавиатур для экранов заказов."""

    @staticmethod
    def pay_action(order_id: int) -> InlineKeyboardMarkup:
        """Клавиатура с кнопкой 'Я оплатил' для нового заказа.

        В итерации 5 заменим на полноценный платёжный flow через Strategy.
        """
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="💰 Я оплатил",
                callback_data=OrderPayCallback(order_id=order_id).pack(),
            )
        )
        return builder.as_markup()
