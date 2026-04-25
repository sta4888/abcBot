from abc import ABC, abstractmethod
from dataclasses import dataclass

from bot.models import Order


@dataclass(frozen=True, slots=True)
class PaymentInitResult:
    """Результат инициации платежа.

    text — что показать пользователю (например, реквизиты, инструкция)
    payment_url — ссылка на оплату от провайдера, если есть (None у заглушек)
    requires_user_action — пользователь должен сам подтвердить оплату нажатием кнопки.
        Для Fake — True, для реальных платёжек — False (статус придёт через webhook)
    """

    text: str
    payment_url: str | None = None
    requires_user_action: bool = False


class PaymentStrategy(ABC):
    """Абстрактный интерфейс платёжной стратегии."""

    # Идентификатор стратегии — должен совпадать с одним из PAYMENT_METHODS
    method_key: str

    @abstractmethod
    async def create_payment(self, order: Order) -> PaymentInitResult:
        """Инициирует платёж для заказа.

        Возвращает данные для отображения пользователю.
        Для Fake — заглушечный текст. Для реальных платёжек — URL/инструкция.
        """

    @abstractmethod
    async def verify_payment(self, order: Order) -> bool:
        """Проверяет, оплачен ли заказ.

        Для Fake — всегда True (доверяем нажатию пользователя).
        Для реальных — запрос статуса у провайдера.
        """
