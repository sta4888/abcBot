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


@dataclass(frozen=True, slots=True)
class CardView:
    """DTO для отображения одной карточки товара в режиме слайдера."""

    product: Product
    category: Category
    page: int  # индекс этого товара в категории, с 0
    total: int  # сколько всего товаров в категории

    @property
    def has_prev(self) -> bool:
        return self.page > 0

    @property
    def has_next(self) -> bool:
        return self.page + 1 < self.total


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

    async def get_product_card(self, category_id: int, page: int) -> CardView | None:
        """Возвращает карточку товара по индексу в категории.

        Используется в режиме слайдера: листаем товары по одному с фото.
        page — индекс с 0.
        """
        category = await self._category_repo.get_by_id(category_id)
        if category is None or not category.is_active:
            return None

        total = await self._product_repo.count_by_category(category_id)
        if total == 0 or page < 0 or page >= total:
            return None

        # Берём ровно один товар, по offset = page
        products = await self._product_repo.list_by_category(
            category_id=category_id,
            limit=1,
            offset=page,
        )
        if not products:
            return None

        return CardView(
            product=products[0],
            category=category,
            page=page,
            total=total,
        )
