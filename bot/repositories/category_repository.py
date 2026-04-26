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

    async def list_all(self) -> list[Category]:
        """Все категории, включая скрытые. Для админских экранов."""
        stmt = select(Category).order_by(Category.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Category | None:
        """Категория по имени (для проверки уникальности)."""
        stmt = select(Category).where(Category.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, category: Category) -> None:
        """Добавляет в сессию. Не делает commit/flush."""
        self._session.add(category)
