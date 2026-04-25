from bot.domain.order_states.base import OrderState, Transition


class NewOrderState(OrderState):
    """Заказ создан, ждёт оплаты.

    Возможные переходы:
    - pay()   → paid
    - cancel() → cancelled
    """

    status_key = "new"

    def pay(self) -> Transition:
        return Transition(new_status="paid", event_name="order.paid")

    def cancel(self) -> Transition:
        return Transition(new_status="cancelled", event_name="order.cancelled")

    @property
    def is_terminal(self) -> bool:
        return False

    @property
    def label(self) -> str:
        return "🆕 Новый"
