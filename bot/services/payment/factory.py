import logging

from bot.config import get_settings
from bot.services.payment.base import PaymentStrategy
from bot.services.payment.fake import FakePaymentStrategy

logger = logging.getLogger(__name__)


class PaymentStrategyFactory:
    """Factory для получения платёжной стратегии по ключу."""

    def __init__(self) -> None:
        self._strategies: dict[str, PaymentStrategy] = {}
        self._register_default()

    def _register_default(self) -> None:
        """Регистрирует все включённые стратегии.

        Fake — всегда. YooKassa — по флагу в конфиге.
        """
        self.register(FakePaymentStrategy())

        if get_settings().yookassa_enabled:
            # Импорт внутри: если флаг выключен — модуль не дёргается.
            # Не критично для перформанса, но красиво показывает изоляцию.
            from bot.services.payment import get_yookassa_client
            from bot.services.payment.yookassa_strategy import (
                YooKassaPaymentStrategy,
            )

            self.register(YooKassaPaymentStrategy(client=get_yookassa_client()))
            logger.info("YooKassa strategy registered")
        else:
            logger.info("YooKassa strategy disabled by config")

    def register(self, strategy: PaymentStrategy) -> None:
        self._strategies[strategy.method_key] = strategy
        logger.debug("Registered payment strategy: %s", strategy.method_key)

    def get(self, method_key: str) -> PaymentStrategy:
        strategy = self._strategies.get(method_key)
        if strategy is None:
            raise KeyError(f"Unknown payment method: {method_key!r}")
        return strategy

    def available_methods(self) -> list[str]:
        return list(self._strategies)
