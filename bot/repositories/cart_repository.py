import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from bot.models import CartItem
from bot.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CartRepository(BaseRepository[CartItem]):
    """Работа с позициями корзины."""

    model_cls = CartItem

    async def list_by_user(self, user_id: int) -> list[CartItem]:
        """Все позиции корзины пользователя с подгруженным товаром.

        selectinload — чтобы не делать N+1 запросов при обращении к item.product.
        """
        stmt = (
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
            .order_by(CartItem.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_product(self, user_id: int, product_id: int) -> CartItem | None:
        """Находит позицию корзины по (user_id, product_id) или None."""
        stmt = select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: int, product_id: int, quantity: int = 1) -> CartItem:
        """Добавляет новую позицию в корзину."""
        item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        self._session.add(item)
        await self._session.flush()
        return item

    async def update_quantity(self, item: CartItem, quantity: int) -> None:
        """Меняет количество. Commit делает вызывающая сторона."""
        item.quantity = quantity
        await self._session.flush()

    async def delete(self, item: CartItem) -> None:
        """Удаляет позицию корзины."""
        await self._session.delete(item)
        await self._session.flush()

    async def clear_user_cart(self, user_id: int) -> None:
        """Удаляет все позиции корзины пользователя (после оформления заказа)."""
        stmt = delete(CartItem).where(CartItem.user_id == user_id)
        await self._session.execute(stmt)
        await self._session.flush()
