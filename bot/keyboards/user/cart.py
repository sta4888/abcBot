from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import (
    CartChangeQtyCallback,
    CartClearCallback,
    CartRemoveCallback,
    CheckoutStartCallback,
)
from bot.services.cart_service import CartLine, CartSummary


class CartKeyboardFactory:
    """Фабрика клавиатур корзины — отвечает за весь интерактив на экране корзины."""

    @staticmethod
    def cart_view(summary: CartSummary) -> InlineKeyboardMarkup:
        """Клавиатура под сообщением корзины.

        Для каждой строки корзины — ряд из четырёх кнопок: −, qty, +, 🗑
        Внизу — кнопки 'Оформить заказ' и 'Очистить'.
        """
        builder = InlineKeyboardBuilder()

        # Ряд кнопок управления для каждой позиции
        for line in summary.lines:
            CartKeyboardFactory._add_line_row(builder, line)

        # Если корзина не пустая — снизу команды
        if not summary.is_empty:
            builder.row(
                InlineKeyboardButton(
                    text="✅ Оформить заказ",
                    callback_data=CheckoutStartCallback().pack(),
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="🗑 Очистить корзину",
                    callback_data=CartClearCallback().pack(),
                )
            )

        return builder.as_markup()

    @staticmethod
    def _add_line_row(builder: InlineKeyboardBuilder, line: CartLine) -> None:
        """Добавляет ряд из четырёх кнопок для одной позиции корзины."""
        builder.row(
            InlineKeyboardButton(
                text="−",
                callback_data=CartChangeQtyCallback(product_id=line.product.id, delta=-1).pack(),
            ),
            InlineKeyboardButton(
                text=str(line.quantity),
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text="+",
                callback_data=CartChangeQtyCallback(product_id=line.product.id, delta=1).pack(),
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=CartRemoveCallback(product_id=line.product.id).pack(),
            ),
        )
