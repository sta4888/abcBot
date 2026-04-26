from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.domain.order_states import (
    InvalidTransitionError,
    OrderState,
    get_order_state,
)
from bot.keyboards.callbacks import (
    OrderCancelConfirmCallback,
    OrderCancelDismissCallback,
    OrderCancelRequestCallback,
    OrderPayCallback,
    UserOrdersListCallback,
    UserOrderViewCallback,
)


class OrdersKeyboardFactory:
    """Фабрика клавиатур для пользовательских экранов заказов."""

    @staticmethod
    def pay_action(order_id: int) -> InlineKeyboardMarkup:
        """Клавиатура с кнопкой 'Я оплатил' для нового заказа."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="💰 Я оплатил",
                callback_data=OrderPayCallback(order_id=order_id).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def payment_url_action(payment_url: str) -> InlineKeyboardMarkup:
        """Кнопка 'Оплатить' с переходом по URL платёжки."""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="💳 Оплатить", url=payment_url))
        return builder.as_markup()

    @staticmethod
    def my_orders_list(orders: list) -> InlineKeyboardMarkup:  # type: ignore[type-arg]
        """Список заказов: каждый — кликабельная кнопка для открытия карточки."""
        builder = InlineKeyboardBuilder()
        for v in orders:
            order = v.order
            state = get_order_state(order.status)
            builder.row(
                InlineKeyboardButton(
                    text=(f"#{order.id} • {state.label} • {order.total / 100:.0f}₽"),
                    callback_data=UserOrderViewCallback(order_id=order.id).pack(),
                )
            )
        return builder.as_markup()

    @staticmethod
    def order_card(order) -> InlineKeyboardMarkup:  # type: ignore[no-untyped-def]
        """Карточка заказа пользователя.

        Кнопка 'Отменить' — только если State разрешает (через TellDontAsk).
        """
        builder = InlineKeyboardBuilder()
        state = get_order_state(order.status)

        # Если заказ ещё не оплачен — кнопка оплаты
        if order.status == "new":
            builder.row(
                InlineKeyboardButton(
                    text="💰 Я оплатил",
                    callback_data=OrderPayCallback(order_id=order.id).pack(),
                )
            )

        # Отмена — если State разрешает
        if OrdersKeyboardFactory._can_cancel(state):
            builder.row(
                InlineKeyboardButton(
                    text="❌ Отменить заказ",
                    callback_data=OrderCancelRequestCallback(order_id=order.id).pack(),
                )
            )

        # Возврат к списку
        builder.row(
            InlineKeyboardButton(
                text="◀️ К заказам",
                callback_data=UserOrdersListCallback().pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def cancel_confirmation(order_id: int) -> InlineKeyboardMarkup:
        """Подтверждение отмены: 'Да, отменить' / 'Нет, оставить'."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✅ Да, отменить",
                callback_data=OrderCancelConfirmCallback(order_id=order_id).pack(),
            ),
            InlineKeyboardButton(
                text="↩️ Нет, оставить",
                callback_data=OrderCancelDismissCallback().pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def _can_cancel(state: OrderState) -> bool:
        """Источник истины — State."""
        try:
            state.cancel()
            return True
        except InvalidTransitionError:
            return False
