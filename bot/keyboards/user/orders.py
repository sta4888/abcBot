from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.domain.order_states import OrderState, get_order_state
from bot.keyboards.callbacks import (
    OrderCancelConfirmCallback,
    OrderCancelDismissCallback,
    OrderCancelRequestCallback,
    OrderPayCallback,
)


class OrdersKeyboardFactory:
    """Фабрика клавиатур для экранов заказов."""

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
    def my_orders_actions(orders: list[tuple[int, str]]) -> InlineKeyboardMarkup:
        """Клавиатура для экрана 'Мои заказы'.

        orders — список (order_id, status). Для каждого активного заказа
        (не терминального) добавляется кнопка 'Отменить'.

        Источник истины — State: добавляем кнопку только если разрешена
        отмена в текущем статусе. Если State меняется — UI следует автоматически.
        """
        builder = InlineKeyboardBuilder()
        for order_id, status in orders:
            state = get_order_state(status)
            if OrdersKeyboardFactory._can_cancel(state):
                builder.row(
                    InlineKeyboardButton(
                        text=f"❌ Отменить #{order_id}",
                        callback_data=OrderCancelRequestCallback(order_id=order_id).pack(),
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
        """Можно ли отменить заказ из текущего состояния.

        Спрашиваем State напрямую: пробуем сделать переход — если падает,
        значит нельзя. Это и есть вся логика проверки в одном месте.
        """
        from bot.domain.order_states import InvalidTransitionError

        try:
            state.cancel()
            return True
        except InvalidTransitionError:
            return False
