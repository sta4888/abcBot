from bot.domain.order_states.base import OrderState
from bot.domain.order_states.cancelled import CancelledOrderState
from bot.domain.order_states.delivered import DeliveredOrderState
from bot.domain.order_states.new import NewOrderState
from bot.domain.order_states.paid import PaidOrderState
from bot.domain.order_states.shipped import ShippedOrderState

# Все известные состояния.
# Каждое — без состояния (stateless), переиспользуем экземпляры.
_STATES: dict[str, OrderState] = {
    "new": NewOrderState(),
    "paid": PaidOrderState(),
    "shipped": ShippedOrderState(),
    "delivered": DeliveredOrderState(),
    "cancelled": CancelledOrderState(),
}


def get_order_state(status: str) -> OrderState:
    """Возвращает объект-состояние по строковому ключу.

    Если статус неизвестен — KeyError. В норме это не должно случаться,
    т.к. БД защищена CheckConstraint-ом.
    """
    try:
        return _STATES[status]
    except KeyError as e:
        raise KeyError(f"Unknown order status: {status!r}") from e
