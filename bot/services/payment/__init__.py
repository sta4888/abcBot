from functools import lru_cache

from bot.services.payment._mock_sdk import YooKassaClient
from bot.services.payment.base import PaymentInitResult, PaymentStrategy
from bot.services.payment.factory import PaymentStrategyFactory
from bot.services.payment.fake import FakePaymentStrategy


@lru_cache(maxsize=1)
def get_payment_factory() -> PaymentStrategyFactory:
    """Возвращает singleton-фабрику платёжных стратегий."""
    return PaymentStrategyFactory()


@lru_cache(maxsize=1)
def get_yookassa_client() -> YooKassaClient:
    """Singleton mock-клиента YooKassa."""
    return YooKassaClient()


__all__ = [
    "FakePaymentStrategy",
    "PaymentInitResult",
    "PaymentStrategy",
    "PaymentStrategyFactory",
    "get_payment_factory",
    "get_yookassa_client",
]
