import logging
import uuid
from datetime import UTC, datetime

from bot.services.payment._mock_sdk.types import Invoice, InvoiceStatus

logger = logging.getLogger(__name__)


class YooKassaError(Exception):
    """Ошибка работы с псевдо-API ЮKassa."""


class YooKassaClient:
    """Псевдо-клиент платёжной системы.

    Отдельные операции:
    - create_invoice() — создаёт инвойс, возвращает payment_url
    - get_invoice(invoice_id) — получить статус и детали
    - mark_invoice_paid(invoice_id) — эмуляция реальной оплаты пользователем
      (в проде это происходит на стороне провайдера, не в нашем коде)
    """

    # Базовый «URL платёжной страницы» — чтоб было что показать юзеру
    _PAYMENT_BASE_URL = "https://mock-yookassa.example.com/pay"

    def __init__(self) -> None:
        self._invoices: dict[str, Invoice] = {}

    def create_invoice(
        self,
        amount_value: int,
        description: str,
        return_url: str | None = None,
    ) -> Invoice:
        """Создаёт новый инвойс. Имитирует POST /payments в реальном API."""
        if amount_value <= 0:
            raise YooKassaError("amount_value must be positive")

        invoice_id = uuid.uuid4().hex
        invoice = Invoice(
            invoice_id=invoice_id,
            amount_value=amount_value,
            description=description,
            status=InvoiceStatus.PENDING,
            payment_url=f"{self._PAYMENT_BASE_URL}/{invoice_id}",
            created_at=datetime.now(UTC),
            return_url=return_url,
        )
        self._invoices[invoice_id] = invoice
        logger.info(
            "[mock-yookassa] Invoice created: id=%s amount=%d desc=%r",
            invoice_id,
            amount_value,
            description,
        )
        return invoice

    def get_invoice(self, invoice_id: str) -> Invoice:
        """Получить детали инвойса. Имитирует GET /payments/{id}."""
        invoice = self._invoices.get(invoice_id)
        if invoice is None:
            raise YooKassaError(f"Invoice not found: {invoice_id}")
        return invoice

    def mark_invoice_paid(self, invoice_id: str) -> Invoice:
        """ЭМУЛЯЦИЯ оплаты пользователем.

        В проде такое происходит на стороне провайдера: пользователь оплатил,
        статус сменился, провайдер шлёт нам webhook. Мы вызываем это вручную
        через админскую команду /mock_pay для учебных целей.
        """
        invoice = self.get_invoice(invoice_id)
        if invoice.status != InvoiceStatus.PENDING:
            raise YooKassaError(f"Invoice {invoice_id} not in pending status (current: {invoice.status.value})")
        invoice.status = InvoiceStatus.SUCCEEDED
        logger.info("[mock-yookassa] Invoice marked paid: id=%s", invoice_id)
        return invoice

    def list_invoices(self) -> list[Invoice]:
        """Все инвойсы — для отладки/админа."""
        return list(self._invoices.values())
