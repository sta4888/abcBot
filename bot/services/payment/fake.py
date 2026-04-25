import logging

from bot.models import Order
from bot.services.payment.base import PaymentInitResult, PaymentStrategy

logger = logging.getLogger(__name__)


class FakePaymentStrategy(PaymentStrategy):
    """Тестовая 'оплата': никаких реальных денег."""

    method_key = "fake"

    async def create_payment(self, order: Order) -> PaymentInitResult:
        """Просто возвращает текст-инструкцию, никакого внешнего вызова."""
        logger.info("Fake payment initiated for order %d", order.id)
        return PaymentInitResult(
            text=(
                f"🧪 <b>Тестовая оплата</b>\n\n"
                f"Заказ <b>#{order.id}</b> на сумму <b>{order.total / 100:.2f}₽</b>.\n\n"
                f"Нажми «💰 Я оплатил», чтобы пометить заказ как оплаченный.\n"
                f"<i>(Это симуляция — реальные деньги не списываются.)</i>"
            ),
            payment_url=None,
            requires_user_action=True,
        )

    async def verify_payment(self, order: Order) -> bool:
        """Для fake — всегда True. Юзер нажал, мы верим."""
        logger.info("Fake payment verified for order %d", order.id)
        return True
