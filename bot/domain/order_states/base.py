from abc import ABC, abstractmethod
from dataclasses import dataclass

# ─── Исключения ───────────────────────────────────────────────────


class InvalidTransitionError(Exception):
    """Запрещённый переход в текущем состоянии."""


# ─── Транзиция ────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Transition:
    """Описание перехода: новый статус + название события для Observer."""

    new_status: str
    event_name: str  # 'order.paid', 'order.shipped', 'order.cancelled' и т.д.


# ─── Базовый State ────────────────────────────────────────────────


class OrderState(ABC):
    """Абстрактный базовый класс состояния заказа.

    Подкласс реализует ровно те методы, которые разрешены в этом состоянии.
    Базовые реализации всех методов — кидают InvalidTransitionError.
    """

    # Идентификатор состояния, должен совпадать со строкой в Order.status
    status_key: str

    def pay(self) -> Transition:
        """Оплата заказа."""
        raise InvalidTransitionError(f"Нельзя оплатить заказ из состояния {self.status_key!r}")

    def ship(self) -> Transition:
        """Отгрузка заказа."""
        raise InvalidTransitionError(f"Нельзя отправить заказ из состояния {self.status_key!r}")

    def deliver(self) -> Transition:
        """Доставка заказа."""
        raise InvalidTransitionError(f"Нельзя пометить как доставленный из состояния {self.status_key!r}")

    def cancel(self) -> Transition:
        """Отмена заказа."""
        raise InvalidTransitionError(f"Нельзя отменить заказ из состояния {self.status_key!r}")

    @property
    @abstractmethod
    def is_terminal(self) -> bool:
        """Конечное ли это состояние (никуда нельзя перейти)."""

    @property
    @abstractmethod
    def label(self) -> str:
        """Человекочитаемое название для UI."""
