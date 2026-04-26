import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.models import Order
from bot.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class OrderRepository(BaseRepository[Order]):
    """Работа с заказами."""

    model_cls = Order

    async def list_by_user(self, user_id: int, limit: int = 20) -> list[Order]:
        """История заказов пользователя — самые свежие сверху."""
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_statuses(self, statuses: Sequence[str], limit: int = 50) -> list[Order]:
        """Заказы с одним из указанных статусов, свежие сверху."""
        stmt = (
            select(Order)
            .where(Order.status.in_(statuses))
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    def add(self, order: Order) -> None:
        """Добавляет заказ в сессию.

        Не делает commit, не делает flush — это решает вызывающая сторона.
        """
        self._session.add(order)
