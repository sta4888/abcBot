import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Order
from bot.repositories.cart_repository import CartRepository
from bot.repositories.order_repository import OrderRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OrderSummaryView:
    """Краткое представление заказа для списка 'Мои заказы'."""

    order: Order
    items_count: int


class OrderService:
    """Фасад над работой с заказами."""

    def __init__(self, session: AsyncSession) -> None:
        self._order_repo = OrderRepository(session)
        self._cart_repo = CartRepository(session)

    async def list_user_orders(self, user_id: int) -> list[OrderSummaryView]:
        """Возвращает заказы пользователя для экрана 'Мои заказы'."""
        orders = await self._order_repo.list_by_user(user_id)
        return [
            OrderSummaryView(
                order=order,
                items_count=sum(item.quantity for item in order.items),
            )
            for order in orders
        ]
