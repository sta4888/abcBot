import pytest

from bot.domain.order_states import (
    CancelledOrderState,
    DeliveredOrderState,
    InvalidTransitionError,
    NewOrderState,
    PaidOrderState,
    ShippedOrderState,
    get_order_state,
)

# ─── NewOrderState ────────────────────────────────────────────────


class TestNewOrderState:
    def test_can_pay(self) -> None:
        transition = NewOrderState().pay()
        assert transition.new_status == "paid"
        assert transition.event_name == "order.paid"

    def test_can_cancel(self) -> None:
        transition = NewOrderState().cancel()
        assert transition.new_status == "cancelled"
        assert transition.event_name == "order.cancelled"

    def test_cannot_ship(self) -> None:
        with pytest.raises(InvalidTransitionError):
            NewOrderState().ship()

    def test_cannot_deliver(self) -> None:
        with pytest.raises(InvalidTransitionError):
            NewOrderState().deliver()

    def test_not_terminal(self) -> None:
        assert NewOrderState().is_terminal is False


# ─── PaidOrderState ───────────────────────────────────────────────


class TestPaidOrderState:
    def test_can_ship(self) -> None:
        transition = PaidOrderState().ship()
        assert transition.new_status == "shipped"

    def test_can_cancel(self) -> None:
        transition = PaidOrderState().cancel()
        assert transition.new_status == "cancelled"

    def test_cannot_pay_twice(self) -> None:
        with pytest.raises(InvalidTransitionError):
            PaidOrderState().pay()

    def test_cannot_deliver(self) -> None:
        with pytest.raises(InvalidTransitionError):
            PaidOrderState().deliver()


# ─── ShippedOrderState ────────────────────────────────────────────


class TestShippedOrderState:
    def test_can_deliver(self) -> None:
        transition = ShippedOrderState().deliver()
        assert transition.new_status == "delivered"

    def test_cannot_cancel(self) -> None:
        # Бизнес-правило: отправленный заказ нельзя отменить
        with pytest.raises(InvalidTransitionError):
            ShippedOrderState().cancel()

    def test_cannot_pay(self) -> None:
        with pytest.raises(InvalidTransitionError):
            ShippedOrderState().pay()


# ─── DeliveredOrderState ──────────────────────────────────────────


class TestDeliveredOrderState:
    def test_is_terminal(self) -> None:
        assert DeliveredOrderState().is_terminal is True

    def test_no_transitions(self) -> None:
        state = DeliveredOrderState()
        for action in ("pay", "ship", "deliver", "cancel"):
            method = getattr(state, action)
            with pytest.raises(InvalidTransitionError):
                method()


# ─── CancelledOrderState ──────────────────────────────────────────


class TestCancelledOrderState:
    def test_is_terminal(self) -> None:
        assert CancelledOrderState().is_terminal is True

    def test_no_transitions(self) -> None:
        state = CancelledOrderState()
        for action in ("pay", "ship", "deliver", "cancel"):
            method = getattr(state, action)
            with pytest.raises(InvalidTransitionError):
                method()


# ─── Точка входа get_order_state ──────────────────────────────────


class TestGetOrderState:
    def test_returns_correct_state(self) -> None:
        assert isinstance(get_order_state("new"), NewOrderState)
        assert isinstance(get_order_state("paid"), PaidOrderState)
        assert isinstance(get_order_state("shipped"), ShippedOrderState)
        assert isinstance(get_order_state("delivered"), DeliveredOrderState)
        assert isinstance(get_order_state("cancelled"), CancelledOrderState)

    def test_unknown_status_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown order status"):
            get_order_state("teleporting")

    def test_returns_same_instance(self) -> None:
        # Singleton-семантика реестра
        assert get_order_state("new") is get_order_state("new")


# ─── Полный жизненный цикл ───────────────────────────────────────


def test_full_happy_path() -> None:
    """Заказ проходит через нормальный цикл: new -> paid -> shipped -> delivered."""
    new_state = NewOrderState()
    t1 = new_state.pay()
    assert t1.new_status == "paid"

    paid_state = get_order_state(t1.new_status)
    t2 = paid_state.ship()
    assert t2.new_status == "shipped"

    shipped_state = get_order_state(t2.new_status)
    t3 = shipped_state.deliver()
    assert t3.new_status == "delivered"

    delivered_state = get_order_state(t3.new_status)
    assert delivered_state.is_terminal


def test_cancel_from_new() -> None:
    """Полный цикл с отменой из new."""
    state = NewOrderState()
    t = state.cancel()
    assert t.new_status == "cancelled"
    assert get_order_state(t.new_status).is_terminal


def test_cancel_from_paid() -> None:
    """Отмена из оплаченного — тоже разрешена."""
    state = PaidOrderState()
    t = state.cancel()
    assert t.new_status == "cancelled"
