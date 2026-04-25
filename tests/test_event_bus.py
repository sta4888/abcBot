from dataclasses import FrozenInstanceError

import pytest

from bot.services.events import EventBus, EventObserver, OrderEvent

# ─── Test double: подписчик-шпион ────────────────────────────────


class SpyObserver(EventObserver):
    """Запоминает, что получил — для проверок в тестах."""

    def __init__(self) -> None:
        self.received: list[OrderEvent] = []

    async def handle(self, event: OrderEvent) -> None:
        self.received.append(event)


class FailingObserver(EventObserver):
    """Всегда кидает исключение."""

    async def handle(self, event: OrderEvent) -> None:
        raise RuntimeError("Boom!")


# ─── EventBus: подписка, публикация ───────────────────────────────


async def test_publish_calls_subscriber() -> None:
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe(spy)

    await bus.publish(OrderEvent(name="order.paid", order_id=42))

    assert len(spy.received) == 1
    assert spy.received[0].name == "order.paid"
    assert spy.received[0].order_id == 42


async def test_publish_calls_all_subscribers() -> None:
    bus = EventBus()
    spy1 = SpyObserver()
    spy2 = SpyObserver()
    bus.subscribe(spy1)
    bus.subscribe(spy2)

    await bus.publish(OrderEvent(name="order.shipped", order_id=1))

    assert len(spy1.received) == 1
    assert len(spy2.received) == 1


async def test_unsubscribe_stops_receiving() -> None:
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe(spy)
    bus.unsubscribe(spy)

    await bus.publish(OrderEvent(name="order.paid", order_id=1))

    assert len(spy.received) == 0


async def test_unsubscribe_unknown_does_not_raise() -> None:
    """Отписка не зарегистрированного — тихая операция."""
    bus = EventBus()
    bus.unsubscribe(SpyObserver())  # просто не падает


async def test_failing_observer_does_not_break_others() -> None:
    """Если один подписчик падает — остальные всё равно получают событие."""
    bus = EventBus()
    failing = FailingObserver()
    spy = SpyObserver()
    bus.subscribe(failing)
    bus.subscribe(spy)

    # Не должно кидать
    await bus.publish(OrderEvent(name="order.paid", order_id=1))

    assert len(spy.received) == 1


async def test_clear_removes_all() -> None:
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe(spy)
    bus.clear()

    await bus.publish(OrderEvent(name="order.paid", order_id=1))

    assert len(spy.received) == 0


# ─── OrderEvent ──────────────────────────────────────────────────


def test_order_event_is_immutable() -> None:
    event = OrderEvent(name="order.paid", order_id=1)
    with pytest.raises(FrozenInstanceError):
        event.name = "order.shipped"  # type: ignore[misc]


# ─── LoggingObserver ─────────────────────────────────────────────


async def test_logging_observer_does_not_raise(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """LoggingObserver просто пишет в лог — не должен падать."""
    import logging

    from bot.services.events.observers import LoggingObserver

    observer = LoggingObserver()
    with caplog.at_level(logging.INFO, logger="bot.services.events.observers.logging"):
        await observer.handle(OrderEvent(name="order.paid", order_id=42))

    assert any("order.paid" in r.message for r in caplog.records)
