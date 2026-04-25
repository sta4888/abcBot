from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderEvent:
    """Событие, связанное с заказом.

    Минимальный конверт: имя события + ID заказа.
    Подписчики при необходимости подгружают данные сами.
    """

    name: str  # 'order.paid', 'order.shipped', 'order.cancelled' и т.д.
    order_id: int


class EventObserver(ABC):
    """Базовый класс для наблюдателей событий заказа."""

    @abstractmethod
    async def handle(self, event: OrderEvent) -> None:
        """Реакция на событие.

        Подписчик сам решает, что делать с конкретным event.name.
        Если событие не интересно — просто return.
        """
