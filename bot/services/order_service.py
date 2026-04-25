import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Order
from bot.repositories.cart_repository import CartRepository
from bot.repositories.order_repository import OrderRepository
from bot.services.order_builder import OrderBuilder

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OrderSummaryView:
    """Краткое представление заказа для списка 'Мои заказы'."""

    order: Order
    items_count: int


# Человекочитаемые названия статусов для UI
STATUS_LABELS = {
    "new": "🆕 Новый",
    "paid": "💰 Оплачен",
    "shipped": "🚚 Отправлен",
    "delivered": "✅ Доставлен",
    "cancelled": "❌ Отменён",
}


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

    async def create_order_from_builder(self, builder: OrderBuilder) -> Order:
        """Создаёт заказ по данным билдера и очищает корзину пользователя.

        Всё в одной транзакции (managed by DatabaseMiddleware):
          1. INSERT orders
          2. INSERT order_items (через cascade на Order.items)
          3. DELETE cart_items
        Если что-то упадёт — middleware откатит всё.
        """
        order = builder.build()
        self._order_repo.add(order)
        # flush, чтобы получить order.id и created_at до commit-а
        await self._order_repo._session.flush()

        await self._cart_repo.clear_user_cart(builder.user_id)

        logger.info(
            "Order created: id=%d user_id=%d total=%.2f₽",
            order.id,
            order.user_id,
            order.total / 100,
        )
        return order

    async def mark_paid(self, order_id: int, user_id: int) -> Order | None:
        """Помечает заказ как оплаченный — заглушка реальной оплаты.

        Возвращает обновлённый Order или None, если:
        - заказ не найден
        - принадлежит другому пользователю
        - не в статусе 'new' (нельзя оплатить дважды)
        """
        order = await self._order_repo.get_by_id(order_id)
        if order is None or order.user_id != user_id:
            return None
        if order.status != "new":
            logger.info(
                "Order %d cannot transition to paid from status=%s",
                order_id,
                order.status,
            )
            return None

        order.status = "paid"
        await self._order_repo._session.flush()
        logger.info("Order %d marked as paid", order_id)
        return order
