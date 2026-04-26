import logging

from bot.models import Order
from bot.services.payment._mock_sdk import (
    InvoiceStatus,
    YooKassaClient,
    YooKassaError,
)
from bot.services.payment.base import PaymentInitResult, PaymentStrategy

logger = logging.getLogger(__name__)


class YooKassaPaymentStrategy(PaymentStrategy):
    """Adapter над псевдо-SDK YooKassa.

    Хранит сопоставление order_id -> invoice_id в памяти.
    В реальном проекте сохранялось бы в Order.external_payment_id.
    """

    method_key = "yookassa"

    def __init__(self, client: YooKassaClient) -> None:
        self._client = client
        # Карта order_id -> invoice_id. В проде — в БД.
        self._order_to_invoice: dict[int, str] = {}

    async def create_payment(self, order: Order) -> PaymentInitResult:
        """Создаём инвойс через SDK, возвращаем PaymentInitResult в нашем формате."""
        try:
            invoice = self._client.create_invoice(
                amount_value=order.total,
                description=f"Заказ #{order.id}",
                return_url=None,
            )
        except YooKassaError as e:
            logger.exception("Failed to create YooKassa invoice")
            raise RuntimeError(f"Не удалось создать платёж: {e}") from e

        # Запоминаем сопоставление: будет нужно для verify
        self._order_to_invoice[order.id] = invoice.invoice_id
        logger.info(
            "YooKassa invoice for order %d: invoice_id=%s url=%s",
            order.id,
            invoice.invoice_id,
            invoice.payment_url,
        )

        text = (
            f"💳 <b>Оплата ЮKassa</b>\n\n"
            f"Заказ <b>#{order.id}</b>\n"
            f"Сумма: <b>{order.total / 100:.2f}₽</b>\n\n"
            f"Перейди по ссылке для оплаты. После оплаты статус обновится "
            f"автоматически (через webhook).\n\n"
            f"<i>Это mock-режим: 'оплату' эмулирует админ командой "
            f"<code>/mock_pay {order.id}</code>.</i>"
        )

        return PaymentInitResult(
            text=text,
            payment_url=invoice.payment_url,
            requires_user_action=False,  # ВАЖНО: статус придёт извне (webhook)
        )

    async def verify_payment(self, order: Order) -> bool:
        """Проверяем статус инвойса в SDK. True — если оплачен."""
        invoice_id = self._order_to_invoice.get(order.id)
        if invoice_id is None:
            logger.warning("verify_payment: no invoice for order %d", order.id)
            return False

        try:
            invoice = self._client.get_invoice(invoice_id)
        except YooKassaError:
            logger.exception("Failed to fetch invoice for order %d", order.id)
            return False

        return invoice.status == InvoiceStatus.SUCCEEDED

    # ─── Доп. метод для эмуляции webhook ─────────────────────────

    async def simulate_webhook_payment(self, order_id: int) -> bool:
        """Эмулирует webhook от ЮKassa: помечает инвойс оплаченным.

        Этого метода НЕТ в базовом PaymentStrategy — он специфичен только для
        mock-режима. В проде webhook прилетает извне, и его принимает HTTP-эндпоинт.
        """
        invoice_id = self._order_to_invoice.get(order_id)
        if invoice_id is None:
            return False
        try:
            self._client.mark_invoice_paid(invoice_id)
        except YooKassaError:
            logger.exception("Failed to mark invoice paid for order %d", order_id)
            return False
        return True
