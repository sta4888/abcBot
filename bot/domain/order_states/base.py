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
    """Абстрактный базовый класс состояния заказа."""

    status_key: str

    # ─── Прямые переходы (как было) ────────────────────────────

    def pay(self) -> Transition:
        raise InvalidTransitionError(f"Нельзя оплатить заказ из состояния {self.status_key!r}")

    def ship(self) -> Transition:
        raise InvalidTransitionError(f"Нельзя отправить заказ из состояния {self.status_key!r}")

    def deliver(self) -> Transition:
        raise InvalidTransitionError(f"Нельзя пометить как доставленный из состояния {self.status_key!r}")

    def cancel(self) -> Transition:
        raise InvalidTransitionError(f"Нельзя отменить заказ из состояния {self.status_key!r}")

    # ─── Обратные переходы (для undo Command) ───────────────────

    def revert_ship(self) -> Transition:
        """Откат отправки: shipped → paid."""
        raise InvalidTransitionError(f"Нельзя откатить отправку из состояния {self.status_key!r}")

    def revert_deliver(self) -> Transition:
        """Откат доставки: delivered → shipped."""
        raise InvalidTransitionError(f"Нельзя откатить доставку из состояния {self.status_key!r}")

    def revert_cancel(self, previous_status: str) -> Transition:
        """Откат отмены: cancelled → previous_status."""
        raise InvalidTransitionError(f"Нельзя откатить отмену из состояния {self.status_key!r}")

    @property
    @abstractmethod
    def is_terminal(self) -> bool: ...

    @property
    @abstractmethod
    def label(self) -> str: ...
