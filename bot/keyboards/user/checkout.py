from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import (
    CheckoutCancelCallback,
    CheckoutConfirmCallback,
    CheckoutDeliveryCallback,
    CheckoutPaymentCallback,
    CheckoutSkipCommentCallback,
    CheckoutSkipPromoCallback,
)

# Человекочитаемые названия методов для UI
DELIVERY_LABELS = {
    "courier": "🚚 Курьером",
    "pickup": "🏬 Самовывоз",
    "post": "📮 Почтой",
}

PAYMENT_LABELS = {
    "fake": "🧪 Тестовая оплата",
    "yookassa": "💳 ЮKassa",
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
        """Выбор способа оплаты — только из тех, что включены в Factory."""
        from bot.services.payment import get_payment_factory

        builder = InlineKeyboardBuilder()
        available = get_payment_factory().available_methods()
        for method in available:
            label = PAYMENT_LABELS.get(method, method)
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

    @staticmethod
    def promo_step() -> InlineKeyboardMarkup:
        """На шаге промокода — 'Без промокода' / 'Отменить'."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="⏭ Без промокода",
                callback_data=CheckoutSkipPromoCallback().pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=CheckoutCancelCallback().pack(),
            )
        )
        return builder.as_markup()
