from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.domain.order_states import (
    InvalidTransitionError,
    OrderState,
    get_order_state,
)
from bot.keyboards.callbacks import (
    AdminOrderActionCallback,
    AdminOrdersListCallback,
    AdminOrderViewCallback,
)
from bot.models import Order

# Действия, которые мы разрешаем админу пробовать
ADMIN_ACTIONS = (
    ("ship", "🚚 Отправить"),
    ("deliver", "✅ Доставлен"),
    ("cancel", "❌ Отменить"),
)

# Фильтры в списке: ключ статуса (или '' для всех активных) → подпись
LIST_FILTERS: tuple[tuple[str, str], ...] = (
    ("", "Все активные"),
    ("new", "🆕 Новые"),
    ("paid", "💰 Оплаченные"),
    ("shipped", "🚚 Отправленные"),
)


class AdminOrdersKeyboardFactory:
    """Фабрика клавиатур для админских экранов заказов."""

    @staticmethod
    def orders_list(orders: list[Order], current_filter: str) -> InlineKeyboardMarkup:
        """Список заказов: фильтры сверху, потом сами заказы."""
        builder = InlineKeyboardBuilder()

        # Ряд фильтров с маркером текущего
        filter_row: list[InlineKeyboardButton] = []
        for key, label in LIST_FILTERS:
            marker = "•" if key == current_filter else ""
            filter_row.append(
                InlineKeyboardButton(
                    text=f"{marker} {label}".strip(),
                    callback_data=AdminOrdersListCallback(status=key).pack(),
                )
            )
        builder.row(*filter_row)

        # Кнопки заказов
        for order in orders:
            state = get_order_state(order.status)
            builder.row(
                InlineKeyboardButton(
                    text=(f"#{order.id} • {state.label} • {order.total / 100:.0f}₽"),
                    callback_data=AdminOrderViewCallback(order_id=order.id).pack(),
                )
            )

        return builder.as_markup()

    @staticmethod
    def order_card(order: Order) -> InlineKeyboardMarkup:
        """Карточка заказа: только разрешённые State действия."""
        builder = InlineKeyboardBuilder()
        state = get_order_state(order.status)

        # Динамически: добавляем кнопку только если State разрешает
        action_row: list[InlineKeyboardButton] = []
        for action_key, label in ADMIN_ACTIONS:
            if AdminOrdersKeyboardFactory._is_action_allowed(state, action_key):
                action_row.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=AdminOrderActionCallback(order_id=order.id, action=action_key).pack(),
                    )
                )
        if action_row:
            builder.row(*action_row)

        # Назад к списку
        builder.row(
            InlineKeyboardButton(
                text="◀️ К списку заказов",
                callback_data=AdminOrdersListCallback().pack(),
            )
        )

        return builder.as_markup()

    @staticmethod
    def _is_action_allowed(state: OrderState, action: str) -> bool:
        """Спрашивает у State, разрешено ли действие.

        Тот же приём, что в пользовательской отмене из итерации 6.
        Источник истины — State-машина.
        """
        method = getattr(state, action, None)
        if method is None:
            return False
        try:
            method()
            return True
        except InvalidTransitionError:
            return False
