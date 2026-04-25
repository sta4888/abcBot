from bot.domain.order_states.base import OrderState


class CancelledOrderState(OrderState):
    """Заказ отменён. Это конечное состояние."""

    status_key = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return True

    @property
    def label(self) -> str:
        return "❌ Отменён"
