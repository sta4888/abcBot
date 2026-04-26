import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Category, Product
from bot.repositories.category_repository import CategoryRepository
from bot.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class AdminCatalogError(Exception):
    """Ошибка операции с каталогом."""


class AdminCatalogService:
    """Админские операции над каталогом."""

    def __init__(self, session: AsyncSession) -> None:
        self._cat_repo = CategoryRepository(session)
        self._prod_repo = ProductRepository(session)

    # ─── Categories ──────────────────────────────────────────────

    async def list_all_categories(self) -> list[Category]:
        return await self._cat_repo.list_all()

    async def get_category(self, category_id: int) -> Category | None:
        return await self._cat_repo.get_by_id(category_id)

    async def create_category(self, name: str, description: str | None) -> Category:
        """Создаёт категорию. Кидает AdminCatalogError, если имя занято."""
        name = name.strip()
        if not name:
            raise AdminCatalogError("Имя категории не может быть пустым")
        if len(name) > 100:
            raise AdminCatalogError("Имя категории слишком длинное (>100)")

        existing = await self._cat_repo.get_by_name(name)
        if existing is not None:
            raise AdminCatalogError(f"Категория с именем {name!r} уже существует")

        category = Category(name=name, description=description)
        self._cat_repo.add(category)
        await self._cat_repo._session.flush()
        logger.info("Created category id=%d name=%r", category.id, name)
        return category

    async def rename_category(self, category_id: int, new_name: str) -> Category | None:
        """Переименование. None — если категория не найдена."""
        new_name = new_name.strip()
        if not new_name:
            raise AdminCatalogError("Имя не может быть пустым")
        if len(new_name) > 100:
            raise AdminCatalogError("Имя слишком длинное (>100)")

        category = await self._cat_repo.get_by_id(category_id)
        if category is None:
            return None

        if new_name == category.name:
            return category  # ничего менять не надо

        existing = await self._cat_repo.get_by_name(new_name)
        if existing is not None and existing.id != category_id:
            raise AdminCatalogError(f"Категория с именем {new_name!r} уже существует")

        category.name = new_name
        await self._cat_repo._session.flush()
        logger.info("Renamed category %d to %r", category_id, new_name)
        return category

    async def toggle_category_active(self, category_id: int) -> Category | None:
        """Переключает is_active. None — если не найдена."""
        category = await self._cat_repo.get_by_id(category_id)
        if category is None:
            return None
        category.is_active = not category.is_active
        await self._cat_repo._session.flush()
        logger.info("Toggled category %d is_active=%s", category_id, category.is_active)
        return category

    # ─── Products ────────────────────────────────────────────────

    async def list_products_in_category(self, category_id: int) -> list[Product]:
        return await self._prod_repo.list_all_by_category(category_id)

    async def get_product(self, product_id: int) -> Product | None:
        return await self._prod_repo.get_by_id(product_id)

    async def create_product(
        self,
        category_id: int,
        name: str,
        description: str,
        price: int,  # в копейках
        stock: int,
        image_file_id: str | None,
    ) -> Product:
        """Создаёт товар. Кидает AdminCatalogError при ошибках валидации."""
        category = await self._cat_repo.get_by_id(category_id)
        if category is None:
            raise AdminCatalogError("Категория не найдена")

        product = Product(
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            stock=stock,
            image_file_id=image_file_id,
        )
        self._prod_repo.add(product)
        await self._prod_repo._session.flush()
        logger.info(
            "Created product id=%d category=%d name=%r",
            product.id,
            category_id,
            name,
        )
        return product

    async def toggle_product_active(self, product_id: int) -> Product | None:
        product = await self._prod_repo.get_by_id(product_id)
        if product is None:
            return None
        product.is_active = not product.is_active
        await self._prod_repo._session.flush()
        return product

    async def change_product_stock(self, product_id: int, delta: int) -> Product | None:
        """Меняет stock на delta. Не уходит ниже 0."""
        product = await self._prod_repo.get_by_id(product_id)
        if product is None:
            return None
        product.stock = max(0, product.stock + delta)
        await self._prod_repo._session.flush()
        return product
