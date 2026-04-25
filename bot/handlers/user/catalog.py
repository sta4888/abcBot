import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.keyboards.callbacks import (
    CatalogBackCallback,
    CategoryCallback,
    ProductCallback,
    ProductCardCallback,
    ProductsListModeCallback,
)
from bot.keyboards.user.catalog import CatalogKeyboardFactory
from bot.keyboards.user.main_menu import BTN_CATALOG
from bot.services.cart_service import CartService
from bot.services.catalog_service import CatalogService, CategoryView

logger = logging.getLogger(__name__)

router = Router(name="user.catalog")


# ─── Главный экран: список категорий ─────────────────────────────────


@router.message(F.text == BTN_CATALOG)
async def show_catalog(message: Message, session: AsyncSession) -> None:
    """Пользователь нажал 'Каталог' → категории, либо сразу одну, если она единственная."""
    catalog = CatalogService(session)
    categories = await catalog.list_categories()

    if not categories:
        await message.answer("В магазине пока нет категорий 😔")
        return

    if len(categories) == 1:
        view = await catalog.get_category_page(categories[0].id, page=0)
        if view is None:
            await message.answer("Категория недоступна.")
            return
        text, kb = _render_products_list(view)
        await message.answer(text, reply_markup=kb)
        return

    kb = CatalogKeyboardFactory.categories_list(categories)
    await message.answer("Выбери категорию:", reply_markup=kb)


# ─── Список товаров категории (режим списка) ─────────────────────────


@router.callback_query(CategoryCallback.filter())
async def show_category(
    callback: CallbackQuery,
    callback_data: CategoryCallback,
    session: AsyncSession,
) -> None:
    """Открыть категорию или перелистать страницу списка."""
    view = await CatalogService(session).get_category_page(
        category_id=callback_data.category_id,
        page=callback_data.page,
    )
    if view is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    text, kb = _render_products_list(view)

    if isinstance(callback.message, Message):
        if callback.message.photo:
            await _replace_photo_with_text(callback.message, text, kb)
        else:
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Детальный экран товара (открыт из списка) ───────────────────────


@router.callback_query(ProductCallback.filter())
async def show_product(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    session: AsyncSession,
) -> None:
    """Открыть классическую карточку товара (текстовую) из списка."""
    if callback.from_user is None:
        await callback.answer()
        return

    product = await CatalogService(session).get_product(callback_data.product_id)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    cart_count = await CartService(session).get_items_count(callback.from_user.id)
    text = _render_product_text(product)
    kb = CatalogKeyboardFactory.product_card(product, cart_items_count=cart_count)

    if isinstance(callback.message, Message):
        if callback.message.photo:
            await _replace_photo_with_text(callback.message, text, kb)
        else:
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Карточка товара в режиме слайдера ───────────────────────────────


@router.callback_query(ProductCardCallback.filter())
async def show_product_card(
    callback: CallbackQuery,
    callback_data: ProductCardCallback,
    session: AsyncSession,
) -> None:
    """Открыть/перелистать карточку товара в режиме слайдера с фото."""
    if callback.from_user is None:
        await callback.answer()
        return

    view = await CatalogService(session).get_product_card(
        category_id=callback_data.category_id,
        page=callback_data.page,
    )
    if view is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    cart_count = await CartService(session).get_items_count(callback.from_user.id)
    caption = _render_product_text(view.product)
    kb = CatalogKeyboardFactory.product_slider_card(view, cart_items_count=cart_count)
    photo = view.product.image_file_id or get_settings().product_placeholder_file_id

    if not photo:
        await callback.answer("Фото не настроено, открываю списком")
        await switch_to_list_inner(callback, view.category.id, session)
        return

    if isinstance(callback.message, Message):
        if callback.message.photo:
            with suppress(TelegramBadRequest):
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=photo, caption=caption),
                    reply_markup=kb,
                )
        else:
            await _replace_text_with_photo(callback.message, photo, caption, kb)
    await callback.answer()


# ─── Переключение из карточек в список ───────────────────────────────


@router.callback_query(ProductsListModeCallback.filter())
async def switch_to_list(
    callback: CallbackQuery,
    callback_data: ProductsListModeCallback,
    session: AsyncSession,
) -> None:
    """Кнопка '📋 Списком' — переключение из режима карточек обратно в список."""
    await switch_to_list_inner(callback, callback_data.category_id, session)


async def switch_to_list_inner(callback: CallbackQuery, category_id: int, session: AsyncSession) -> None:
    """Внутренняя реализация переключения в список."""
    view = await CatalogService(session).get_category_page(category_id, page=0)
    if view is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    text, kb = _render_products_list(view)

    if isinstance(callback.message, Message):
        if callback.message.photo:
            await _replace_photo_with_text(callback.message, text, kb)
        else:
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Возврат к категориям ────────────────────────────────────────────


@router.callback_query(CatalogBackCallback.filter())
async def back_to_categories(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Возврат к списку категорий из любого места каталога."""
    categories = await CatalogService(session).list_categories()
    kb = CatalogKeyboardFactory.categories_list(categories)
    text = "Выбери категорию:"

    if isinstance(callback.message, Message):
        if callback.message.photo:
            await _replace_photo_with_text(callback.message, text, kb)
        else:
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Заглушка noop ──────────────────────────────────────────────────


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    """Кнопка-индикатор (1/3) — ничего не делает."""
    await callback.answer()


# ─── Утилиты рендеринга ─────────────────────────────────────────────


def _render_products_list(
    view: CategoryView,
) -> tuple[str, InlineKeyboardMarkup]:
    """Текст и клавиатура для экрана списка товаров."""
    if not view.products_page.items:
        text = f"В категории <b>{view.category.name}</b> пока нет товаров."
    else:
        text = f"<b>{view.category.name}</b>\nВыбери товар:"
    kb = CatalogKeyboardFactory.products_list(
        category_id=view.category.id,
        products_page=view.products_page,
    )
    return text, kb


def _render_product_text(product: object) -> str:
    """Текст карточки товара — единый формат для списка и слайдера."""
    return (
        f"<b>{product.name}</b>\n\n"  # type: ignore[attr-defined]
        f"{product.description}\n\n"  # type: ignore[attr-defined]
        f"💰 Цена: <b>{product.price_rub:.2f}₽</b>\n"  # type: ignore[attr-defined]
        f"📦 В наличии: <b>{product.stock} шт.</b>"  # type: ignore[attr-defined]
    )


async def _replace_photo_with_text(message: Message, text: str, kb: InlineKeyboardMarkup) -> None:
    """Удаляет фото-сообщение и шлёт новое текстовое в тот же чат."""
    with suppress(TelegramBadRequest):
        await message.delete()
    await message.answer(text, reply_markup=kb)


async def _replace_text_with_photo(message: Message, photo: str, caption: str, kb: InlineKeyboardMarkup) -> None:
    """Удаляет текстовое сообщение и шлёт новое с фото в тот же чат."""
    with suppress(TelegramBadRequest):
        await message.delete()
    await message.answer_photo(photo=photo, caption=caption, reply_markup=kb)
