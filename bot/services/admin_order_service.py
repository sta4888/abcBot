import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Order
from bot.repositories.order_repository import OrderRepository

logger = logging.getLogger(__name__)

# Активные = не терминальные. Если статусов добавится — обновится здесь.
ACTIVE_STATUSES = ("new", "paid", "shipped")


class AdminOrderService:
    """Админские запросы к заказам.

    Изменения статусов идут через основной OrderService (ship_order,
    deliver_order, cancel_order) — не дублируем State-логику.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._order_repo = OrderRepository(session)

    async def list_orders(self, statuses: Sequence[str] | None = None, limit: int = 50) -> list[Order]:
        """Заказы по статусу. Если None — активные (не терминальные)."""
        if statuses is None:
            statuses = ACTIVE_STATUSES
        return await self._order_repo.list_by_statuses(statuses, limit=limit)

    async def get_order(self, order_id: int) -> Order | None:
        return await self._order_repo.get_by_id(order_id)
