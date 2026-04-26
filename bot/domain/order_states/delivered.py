from bot.domain.order_states.base import OrderState, Transition


class DeliveredOrderState(OrderState):
    """Заказ доставлен. Терминальное в нормальном потоке, но можно откатить."""

    status_key = "delivered"

    def revert_deliver(self) -> Transition:
        """Откат доставки: возврат в 'shipped' (если админ ошибся)."""
        return Transition(new_status="shipped", event_name="order.deliver_reverted")

    @property
    def is_terminal(self) -> bool:
        return True  # для UI кнопки 'отменить' и т.п. — терминальное

    @property
    def label(self) -> str:
        return "✅ Доставлен"
