from bot.domain.order_states.base import OrderState, Transition


class ShippedOrderState(OrderState):
    """Заказ в пути.

    Возможные переходы:
    - deliver() → delivered
    - revert_ship() → paid (откат админа)
    """

    status_key = "shipped"

    def deliver(self) -> Transition:
        return Transition(new_status="delivered", event_name="order.delivered")

    def revert_ship(self) -> Transition:
        return Transition(new_status="paid", event_name="order.ship_reverted")

    @property
    def is_terminal(self) -> bool:
        return False

    @property
    def label(self) -> str:
        return "🚚 Отправлен"
