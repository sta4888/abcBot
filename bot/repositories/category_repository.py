import logging

from sqlalchemy import select

from bot.models import Category
from bot.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository[Category]):
    """Работа с категориями товаров."""

    model_cls = Category

    async def list_active(self) -> list[Category]:
        """Все активные категории, отсортированные по имени."""
        stmt = select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
