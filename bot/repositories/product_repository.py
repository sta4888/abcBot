import logging

from sqlalchemy import func, select

from bot.models import Product
from bot.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository[Product]):
    """Работа с товарами каталога."""

    model_cls = Product

    async def list_by_category(
        self,
        category_id: int,
        limit: int,
        offset: int,
    ) -> list[Product]:
        """Активные товары категории с пагинацией."""
        stmt = (
            select(Product)
            .where(
                Product.category_id == category_id,
                Product.is_active.is_(True),
            )
            .order_by(Product.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_by_category(self, category_id: int) -> list[Product]:
        """Все товары категории, включая неактивные. Для админки."""
        stmt = select(Product).where(Product.category_id == category_id).order_by(Product.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_category(self, category_id: int) -> int:
        """Сколько активных товаров в категории."""
        stmt = (
            select(func.count())
            .select_from(Product)
            .where(
                Product.category_id == category_id,
                Product.is_active.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    def add(self, product: Product) -> None:
        """Добавляет в сессию."""
        self._session.add(product)

    async def get_for_update(self, product_id: int) -> Product | None:
        """Загрузить Product с SELECT FOR UPDATE.

        Используется при создании заказа: блокирует строку до конца транзакции,
        чтобы другие транзакции не могли изменить stock параллельно.
        """
        stmt = select(Product).where(Product.id == product_id).with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
