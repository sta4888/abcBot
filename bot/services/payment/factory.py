import logging

from bot.services.payment.base import PaymentStrategy
from bot.services.payment.fake import FakePaymentStrategy

logger = logging.getLogger(__name__)


class PaymentStrategyFactory:
    """Factory для получения платёжной стратегии по ключу.

    Регистрация всех стратегий — один раз в момент создания фабрики.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, PaymentStrategy] = {}
        self._register_default()

    def _register_default(self) -> None:
        """Регистрирует все известные стратегии.

        В будущем сюда добавятся YooKassaPaymentStrategy, StripePaymentStrategy и т.д.
        """
        self.register(FakePaymentStrategy())

    def register(self, strategy: PaymentStrategy) -> None:
        """Регистрирует стратегию в реестре."""
        self._strategies[strategy.method_key] = strategy
        logger.debug("Registered payment strategy: %s", strategy.method_key)

    def get(self, method_key: str) -> PaymentStrategy:
        """Возвращает стратегию по ключу или KeyError, если не найдена."""
        strategy = self._strategies.get(method_key)
        if strategy is None:
            raise KeyError(f"Unknown payment method: {method_key!r}")
        return strategy

    def available_methods(self) -> list[str]:
        """Список ключей всех зарегистрированных стратегий."""
        return list(self._strategies)
