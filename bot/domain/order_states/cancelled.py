from bot.domain.order_states.base import OrderState, Transition


class CancelledOrderState(OrderState):
    """Заказ отменён. Можно откатить — вернуть в предыдущий статус."""

    status_key = "cancelled"

    def revert_cancel(self, previous_status: str) -> Transition:
        """Откат отмены: возврат в статус до отмены.

        previous_status сохраняется командой при выполнении.
        """
        if previous_status not in ("new", "paid", "shipped"):
            raise ValueError(f"Cannot revert to terminal status {previous_status!r}")
        return Transition(new_status=previous_status, event_name="order.cancel_reverted")

    @property
    def is_terminal(self) -> bool:
        return True

    @property
    def label(self) -> str:
        return "❌ Отменён"
