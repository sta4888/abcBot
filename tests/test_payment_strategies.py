import pytest

from bot.models import Order
from bot.services.payment import (
    FakePaymentStrategy,
    PaymentStrategyFactory,
    get_payment_factory,
)
from bot.services.payment.base import PaymentInitResult, PaymentStrategy


@pytest.fixture
def fake_order() -> Order:
    """Создаём минимальный Order вручную, без БД — для тестов стратегий.

    Поля required для стратегий: id, total, payment_method.
    """
    order = Order()
    order.id = 42
    order.user_id = 1
    order.total = 99900
    order.delivery_method = "courier"
    order.delivery_address = "Тестовый адрес"
    order.contact_phone = "+79991234567"
    order.payment_method = "fake"
    order.status = "new"
    order.comment = None
    return order


# ─── FakePaymentStrategy ──────────────────────────────────────────


async def test_fake_create_payment_returns_init_result(
    fake_order: Order,
) -> None:
    strategy = FakePaymentStrategy()
    result = await strategy.create_payment(fake_order)

    assert isinstance(result, PaymentInitResult)
    assert "42" in result.text  # id заказа в тексте
    assert result.payment_url is None  # нет URL у фейковой
    assert result.requires_user_action is True


async def test_fake_verify_always_returns_true(fake_order: Order) -> None:
    strategy = FakePaymentStrategy()
    assert await strategy.verify_payment(fake_order) is True


def test_fake_method_key() -> None:
    strategy = FakePaymentStrategy()
    assert strategy.method_key == "fake"


# ─── PaymentStrategyFactory ───────────────────────────────────────


def test_factory_returns_fake_for_known_method() -> None:
    factory = PaymentStrategyFactory(yookassa_enabled=False)
    strategy = factory.get("fake")
    assert isinstance(strategy, FakePaymentStrategy)


def test_factory_raises_for_unknown_method() -> None:
    factory = PaymentStrategyFactory(yookassa_enabled=False)
    with pytest.raises(KeyError, match="Unknown payment method"):
        factory.get("bitcoin")


def test_factory_lists_available_methods() -> None:
    factory = PaymentStrategyFactory(yookassa_enabled=False)
    assert "fake" in factory.available_methods()


def test_factory_register_custom_strategy() -> None:
    """Можно зарегистрировать любую кастомную стратегию."""

    class CustomStrategy(PaymentStrategy):
        method_key = "custom"

        async def create_payment(self, order: Order) -> PaymentInitResult:
            return PaymentInitResult(text="custom")

        async def verify_payment(self, order: Order) -> bool:
            return False

    factory = PaymentStrategyFactory(yookassa_enabled=False)
    factory.register(CustomStrategy())

    strategy = factory.get("custom")
    assert isinstance(strategy, CustomStrategy)
    assert "custom" in factory.available_methods()


# ─── Singleton ─────────────────────────────────────────────────────


def test_get_payment_factory_returns_same_instance() -> None:
    """Singleton-семантика lru_cache.

    Этот тест требует валидного .env (читает Settings).
    В CI без .env пропускаем — остальная Factory покрыта без зависимости от конфига.
    """
    import os

    if not os.getenv("BOT__TOKEN"):
        pytest.skip("Skipping: requires .env (BOT__TOKEN not set)")

    factory1 = get_payment_factory()
    factory2 = get_payment_factory()
    assert factory1 is factory2
