import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.callbacks import (
    CatalogBackCallback,
    CategoryCallback,
    ProductCallback,
)
from bot.keyboards.user.catalog import CatalogKeyboardFactory
from bot.keyboards.user.main_menu import BTN_CATALOG
from bot.repositories.category_repository import CategoryRepository
from bot.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)

router = Router(name="user.catalog")

# Пока без пагинации — показываем все товары категории разом.
# Пагинация появится в этапе 3.
PRODUCTS_LIMIT = 50


@router.message(F.text == BTN_CATALOG)
async def show_catalog(message: Message, session: AsyncSession) -> None:
    """Пользователь нажал кнопку 'Каталог' → показываем категории."""
    categories = await CategoryRepository(session).list_active()
    if not categories:
        await message.answer("В магазине пока нет категорий 😔")
        return

    kb = CatalogKeyboardFactory.categories_list(categories)
    await message.answer("Выбери категорию:", reply_markup=kb)


@router.callback_query(CategoryCallback.filter())
async def show_category(
    callback: CallbackQuery,
    callback_data: CategoryCallback,
    session: AsyncSession,
) -> None:
    """Пользователь выбрал категорию → показываем товары."""
    category_repo = CategoryRepository(session)
    product_repo = ProductRepository(session)

    category = await category_repo.get_by_id(callback_data.category_id)
    if category is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    products = await product_repo.list_by_category(
        category_id=category.id,
        limit=PRODUCTS_LIMIT,
        offset=0,
    )

    if not products:
        text = f"В категории <b>{category.name}</b> пока нет товаров."
    else:
        text = f"<b>{category.name}</b>\nВыбери товар:"

    kb = CatalogKeyboardFactory.products_list(products)

    # Редактируем сообщение вместо отправки нового — так чат не мусорится.
    # isinstance-проверка нужна из-за типа Message | InaccessibleMessage | None:
    # старые (48ч+) или удалённые сообщения нельзя редактировать.
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(ProductCallback.filter())
async def show_product(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    session: AsyncSession,
) -> None:
    """Пользователь открыл карточку товара."""
    product = await ProductRepository(session).get_by_id(callback_data.product_id)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = (
        f"<b>{product.name}</b>\n\n"
        f"{product.description}\n\n"
        f"💰 Цена: <b>{product.price_rub:.2f}₽</b>\n"
        f"📦 В наличии: <b>{product.stock} шт.</b>"
    )

    kb = CatalogKeyboardFactory.product_card(product)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(CatalogBackCallback.filter())
async def back_to_categories(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Кнопка 'Назад' на списке товаров — возврат к категориям."""
    categories = await CategoryRepository(session).list_active()
    kb = CatalogKeyboardFactory.categories_list(categories)

    if isinstance(callback.message, Message):
        await callback.message.edit_text("Выбери категорию:", reply_markup=kb)
    await callback.answer()
