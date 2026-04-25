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
from bot.services.catalog_service import CatalogService

logger = logging.getLogger(__name__)

router = Router(name="user.catalog")


@router.message(F.text == BTN_CATALOG)
async def show_catalog(message: Message, session: AsyncSession) -> None:
    """Пользователь нажал кнопку 'Каталог' → показываем категории."""
    categories = await CatalogService(session).list_categories()
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
    """Пользователь выбрал категорию или листает её страницы → показываем товары."""
    view = await CatalogService(session).get_category_page(
        category_id=callback_data.category_id,
        page=callback_data.page,
    )
    if view is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    if not view.products_page.items:
        text = f"В категории <b>{view.category.name}</b> пока нет товаров."
    else:
        text = f"<b>{view.category.name}</b>\nВыбери товар:"

    kb = CatalogKeyboardFactory.products_list(
        category_id=view.category.id,
        products_page=view.products_page,
    )

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
    product = await CatalogService(session).get_product(callback_data.product_id)
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
    categories = await CatalogService(session).list_categories()
    kb = CatalogKeyboardFactory.categories_list(categories)

    if isinstance(callback.message, Message):
        await callback.message.edit_text("Выбери категорию:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    """Индикатор страницы пагинации — кнопка не должна ничего делать."""
    await callback.answer()
