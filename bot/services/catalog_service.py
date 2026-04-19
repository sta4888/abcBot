import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Category, Product
from bot.repositories.category_repository import CategoryRepository
from bot.repositories.product_repository import ProductRepository
from bot.utils.pagination import Page

logger = logging.getLogger(__name__)

# Сколько товаров показывать на одной странице.
# Выносим в константу, чтобы легко менять в одном месте.
PRODUCTS_PER_PAGE = 5


@dataclass(frozen=True, slots=True)
class CategoryView:
    """DTO для хендлера: категория + её товары (страница)."""

    category: Category
    products_page: Page[Product]


class CatalogService:
    """Фасад над работой с каталогом (категории + товары)."""

    def __init__(self, session: AsyncSession) -> None:
        self._category_repo = CategoryRepository(session)
        self._product_repo = ProductRepository(session)

    async def list_categories(self) -> list[Category]:
        """Все активные категории."""
        return await self._category_repo.list_active()

    async def get_category_page(self, category_id: int, page: int = 0) -> CategoryView | None:
        """Возвращает категорию с её товарами на указанной странице.

        None — если категория не найдена или неактивна.
        """
        category = await self._category_repo.get_by_id(category_id)
        if category is None or not category.is_active:
            logger.info("Category %d not found or inactive", category_id)
            return None

        # Считаем total и достаём нужный слайс
        total = await self._product_repo.count_by_category(category_id)
        offset = page * PRODUCTS_PER_PAGE
        products = await self._product_repo.list_by_category(
            category_id=category_id,
            limit=PRODUCTS_PER_PAGE,
            offset=offset,
        )

        products_page = Page(
            items=products,
            page=page,
            page_size=PRODUCTS_PER_PAGE,
            total=total,
        )

        return CategoryView(category=category, products_page=products_page)

    async def get_product(self, product_id: int) -> Product | None:
        """Товар по id или None."""
        return await self._product_repo.get_by_id(product_id)
