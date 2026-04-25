from bot.domain.order_states.base import OrderState


class DeliveredOrderState(OrderState):
    """Заказ доставлен. Это конечное состояние."""

    status_key = "delivered"

    @property
    def is_terminal(self) -> bool:
        return True

    @property
    def label(self) -> str:
        return "✅ Доставлен"
