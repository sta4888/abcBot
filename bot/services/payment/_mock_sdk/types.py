from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class InvoiceStatus(StrEnum):
    """Статус инвойса в платёжной системе."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"


@dataclass
class Invoice:
    """Сущность инвойса в SDK.

    Поля специально называются 'не как у нас': amount_value (а не price),
    invoice_id (а не order_id), payment_url (формируется самим SDK).
    """

    invoice_id: str
    amount_value: int  # в копейках
    description: str
    status: InvoiceStatus
    payment_url: str
    created_at: datetime
    return_url: str | None = None
