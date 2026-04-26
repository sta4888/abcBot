from collections.abc import Sequence

from bot.services.discounts.base import PriceCalculator
from bot.services.order_builder import OrderItemSpec


class BaseTotal(PriceCalculator):
    """Корень цепочки: возвращает сумму без скидок.

    Это не Decorator — это терминальный объект. Декораторы оборачивают его.
    """

    def __init__(self, items: Sequence[OrderItemSpec]) -> None:
        self._items = list(items)

    def calculate(self) -> int:
        return sum(item.price * item.quantity for item in self._items)
