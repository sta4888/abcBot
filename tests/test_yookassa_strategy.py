import pytest

from bot.models import Order
from bot.services.payment._mock_sdk import (
    InvoiceStatus,
    YooKassaClient,
    YooKassaError,
)
from bot.services.payment.base import PaymentInitResult
from bot.services.payment.yookassa_strategy import YooKassaPaymentStrategy


@pytest.fixture
def fake_order() -> Order:
    order = Order()
    order.id = 1
    order.user_id = 1
    order.total = 50000  # 500₽
    order.delivery_method = "courier"
    order.delivery_address = "Адрес"
    order.contact_phone = "+79991234567"
    order.payment_method = "yookassa"
    order.status = "new"
    order.comment = None
    return order


# ─── SDK ─────────────────────────────────────────────────────────


def test_sdk_create_invoice() -> None:
    client = YooKassaClient()
    invoice = client.create_invoice(amount_value=10000, description="Test")
    assert invoice.amount_value == 10000
    assert invoice.status == InvoiceStatus.PENDING
    assert invoice.payment_url.startswith("https://")


def test_sdk_negative_amount_rejected() -> None:
    client = YooKassaClient()
    with pytest.raises(YooKassaError):
        client.create_invoice(amount_value=0, description="X")


def test_sdk_get_unknown_invoice() -> None:
    client = YooKassaClient()
    with pytest.raises(YooKassaError, match="not found"):
        client.get_invoice("nonexistent")


def test_sdk_mark_paid_changes_status() -> None:
    client = YooKassaClient()
    invoice = client.create_invoice(amount_value=10000, description="Test")

    paid = client.mark_invoice_paid(invoice.invoice_id)
    assert paid.status == InvoiceStatus.SUCCEEDED


def test_sdk_cannot_mark_paid_twice() -> None:
    client = YooKassaClient()
    invoice = client.create_invoice(amount_value=10000, description="Test")
    client.mark_invoice_paid(invoice.invoice_id)

    with pytest.raises(YooKassaError, match="not in pending"):
        client.mark_invoice_paid(invoice.invoice_id)


# ─── Adapter ────────────────────────────────────────────────────


async def test_adapter_create_payment(fake_order: Order) -> None:
    client = YooKassaClient()
    strategy = YooKassaPaymentStrategy(client=client)

    result = await strategy.create_payment(fake_order)

    assert isinstance(result, PaymentInitResult)
    assert result.payment_url is not None
    assert result.payment_url.startswith("https://")
    assert result.requires_user_action is False
    assert "500.00" in result.text


async def test_adapter_verify_unpaid(fake_order: Order) -> None:
    """До оплаты verify возвращает False."""
    client = YooKassaClient()
    strategy = YooKassaPaymentStrategy(client=client)
    await strategy.create_payment(fake_order)

    assert await strategy.verify_payment(fake_order) is False


async def test_adapter_verify_paid(fake_order: Order) -> None:
    """После эмуляции webhook verify возвращает True."""
    client = YooKassaClient()
    strategy = YooKassaPaymentStrategy(client=client)
    await strategy.create_payment(fake_order)

    success = await strategy.simulate_webhook_payment(fake_order.id)
    assert success is True

    assert await strategy.verify_payment(fake_order) is True


async def test_adapter_verify_unknown_order(fake_order: Order) -> None:
    """Если для заказа не было create_payment, verify = False."""
    client = YooKassaClient()
    strategy = YooKassaPaymentStrategy(client=client)
    # пропускаем create_payment

    assert await strategy.verify_payment(fake_order) is False


async def test_adapter_simulate_unknown_order() -> None:
    """simulate_webhook_payment для незнакомого заказа возвращает False."""
    client = YooKassaClient()
    strategy = YooKassaPaymentStrategy(client=client)

    assert await strategy.simulate_webhook_payment(99999) is False


def test_adapter_method_key() -> None:
    client = YooKassaClient()
    strategy = YooKassaPaymentStrategy(client=client)
    assert strategy.method_key == "yookassa"
