from bot.domain.order_states.base import OrderState, Transition


class PaidOrderState(OrderState):
    """Заказ оплачен, ждёт отгрузки.

    Возможные переходы:
    - ship()   → shipped
    - cancel() → cancelled  (отмена с возвратом средств)
    """

    status_key = "paid"

    def ship(self) -> Transition:
        return Transition(new_status="shipped", event_name="order.shipped")

    def cancel(self) -> Transition:
        return Transition(new_status="cancelled", event_name="order.cancelled")

    @property
    def is_terminal(self) -> bool:
        return False

    @property
    def label(self) -> str:
        return "💰 Оплачен"
