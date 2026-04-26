import logging

from bot.services.payment.base import PaymentStrategy
from bot.services.payment.fake import FakePaymentStrategy

logger = logging.getLogger(__name__)


class PaymentStrategyFactory:
    """Factory для получения платёжной стратегии по ключу."""

    def __init__(self, yookassa_enabled: bool | None = None) -> None:
        """Создаёт фабрику.

        yookassa_enabled — None означает 'читать из конфига'.
        Явное True/False позволяет создать фабрику для тестов без .env.
        """
        self._strategies: dict[str, PaymentStrategy] = {}
        self._register_default(yookassa_enabled)

    def _register_default(self, yookassa_enabled: bool | None) -> None:
        """Регистрирует все включённые стратегии."""
        self.register(FakePaymentStrategy())

        # Определяем флаг: если не передан явно — читаем из конфига
        if yookassa_enabled is None:
            from bot.config import get_settings

            yookassa_enabled = get_settings().yookassa_enabled

        if yookassa_enabled:
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
