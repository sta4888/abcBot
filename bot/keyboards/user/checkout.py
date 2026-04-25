from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import (
    CheckoutCancelCallback,
    CheckoutConfirmCallback,
    CheckoutDeliveryCallback,
    CheckoutPaymentCallback,
    CheckoutSkipCommentCallback,
)

# Человекочитаемые названия методов для UI
DELIVERY_LABELS = {
    "courier": "🚚 Курьером",
    "pickup": "🏬 Самовывоз",
    "post": "📮 Почтой",
}

PAYMENT_LABELS = {
    "fake": "🧪 Тестовая оплата",
    # 'yookassa': '💳 ЮKassa',  — в итерации 8
    # 'stripe': '💳 Stripe',    — в итерации 8
}


class CheckoutKeyboardFactory:
    """Фабрика клавиатур для шагов оформления."""

    @staticmethod
    def cancel_only() -> InlineKeyboardMarkup:
        """Клавиатура с одной кнопкой 'Отменить' — для текстовых шагов."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить оформление",
                callback_data=CheckoutCancelCallback().pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def delivery_methods() -> InlineKeyboardMarkup:
        """Выбор способа доставки."""
        builder = InlineKeyboardBuilder()
        for method, label in DELIVERY_LABELS.items():
            builder.button(
                text=label,
                callback_data=CheckoutDeliveryCallback(method=method),
            )
        builder.adjust(1)
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=CheckoutCancelCallback().pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def payment_methods() -> InlineKeyboardMarkup:
        """Выбор способа оплаты."""
        builder = InlineKeyboardBuilder()
        for method, label in PAYMENT_LABELS.items():
            builder.button(
                text=label,
                callback_data=CheckoutPaymentCallback(method=method),
            )
        builder.adjust(1)
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=CheckoutCancelCallback().pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def comment_step() -> InlineKeyboardMarkup:
        """На шаге комментария — 'Пропустить' и 'Отменить'."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="⏭ Без комментария",
                callback_data=CheckoutSkipCommentCallback().pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=CheckoutCancelCallback().pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def confirmation() -> InlineKeyboardMarkup:
        """Шаг подтверждения: 'Подтвердить' / 'Отменить'."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✅ Подтвердить заказ",
                callback_data=CheckoutConfirmCallback().pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=CheckoutCancelCallback().pack(),
            )
        )
        return builder.as_markup()
