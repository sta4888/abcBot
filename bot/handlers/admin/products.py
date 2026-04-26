import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin.catalog import AdminCatalogKeyboardFactory
from bot.keyboards.callbacks import (
    AdminProductAddCallback,
    AdminProductEditCallback,
    AdminProductsShowCallback,
    AdminProductStockCallback,
    AdminProductToggleCallback,
)
from bot.services.admin_catalog_service import (
    AdminCatalogError,
    AdminCatalogService,
)
from bot.services.product_builder import ProductBuilder, ProductBuilderError
from bot.states.admin import AdminProductFSM

logger = logging.getLogger(__name__)

router = Router(name="admin.products")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


# ─── Список товаров категории ─────────────────────────────────


@router.callback_query(AdminProductsShowCallback.filter())
async def show_products(
    callback: CallbackQuery,
    callback_data: AdminProductsShowCallback,
    session: AsyncSession,
) -> None:
    service = AdminCatalogService(session)
    cat = await service.get_category(callback_data.category_id)
    if cat is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    products = await service.list_products_in_category(callback_data.category_id)
    text = _format_products_text(cat, products)
    kb = AdminCatalogKeyboardFactory.products_list(cat, products)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Карточка товара ───────────────────────────────────────────


@router.callback_query(AdminProductEditCallback.filter())
async def show_product_card(
    callback: CallbackQuery,
    callback_data: AdminProductEditCallback,
    session: AsyncSession,
) -> None:
    product = await AdminCatalogService(session).get_product(callback_data.product_id)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = _format_product_text(product)
    kb = AdminCatalogKeyboardFactory.product_card(product)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Toggle ────────────────────────────────────────────────────


@router.callback_query(AdminProductToggleCallback.filter())
async def toggle_product(
    callback: CallbackQuery,
    callback_data: AdminProductToggleCallback,
    session: AsyncSession,
) -> None:
    product = await AdminCatalogService(session).toggle_product_active(callback_data.product_id)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = _format_product_text(product)
    kb = AdminCatalogKeyboardFactory.product_card(product)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Товар скрыт" if not product.is_active else "Товар показан")


# ─── Stock ─────────────────────────────────────────────────────


@router.callback_query(AdminProductStockCallback.filter())
async def change_stock(
    callback: CallbackQuery,
    callback_data: AdminProductStockCallback,
    session: AsyncSession,
) -> None:
    product = await AdminCatalogService(session).change_product_stock(callback_data.product_id, callback_data.delta)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = _format_product_text(product)
    kb = AdminCatalogKeyboardFactory.product_card(product)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer(f"Остаток: {product.stock}")


# ─── Добавление товара (FSM с Builder) ─────────────────────────


@router.callback_query(AdminProductAddCallback.filter())
async def add_product_start(
    callback: CallbackQuery,
    callback_data: AdminProductAddCallback,
    state: FSMContext,
) -> None:
    await state.set_state(AdminProductFSM.waiting_name)
    await state.update_data(category_id=callback_data.category_id)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "🛍 <b>Новый товар</b>\n\nШаг 1/5: введи <b>название</b>.",
            reply_markup=AdminCatalogKeyboardFactory.cancel_only(),
        )
    await callback.answer()


@router.message(AdminProductFSM.waiting_name, F.text)
async def add_product_name(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    builder = await _restore_builder(state)
    try:
        builder.set_name(message.text)
    except ProductBuilderError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await _save_builder(state, builder)
    await state.set_state(AdminProductFSM.waiting_description)
    await message.answer(
        "Шаг 2/5: введи <b>описание</b> товара.",
        reply_markup=AdminCatalogKeyboardFactory.cancel_only(),
    )


@router.message(AdminProductFSM.waiting_description, F.text)
async def add_product_description(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    builder = await _restore_builder(state)
    try:
        builder.set_description(message.text)
    except ProductBuilderError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await _save_builder(state, builder)
    await state.set_state(AdminProductFSM.waiting_price)
    await message.answer(
        "Шаг 3/5: введи <b>цену в рублях</b> (например: <code>199</code> или <code>149.99</code>).",
        reply_markup=AdminCatalogKeyboardFactory.cancel_only(),
    )


@router.message(AdminProductFSM.waiting_price, F.text)
async def add_product_price(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    builder = await _restore_builder(state)
    try:
        builder.set_price_rub(message.text)
    except ProductBuilderError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await _save_builder(state, builder)
    await state.set_state(AdminProductFSM.waiting_stock)
    await message.answer(
        "Шаг 4/5: введи <b>остаток</b> на складе (целое число).",
        reply_markup=AdminCatalogKeyboardFactory.cancel_only(),
    )


@router.message(AdminProductFSM.waiting_stock, F.text)
async def add_product_stock(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    builder = await _restore_builder(state)
    try:
        builder.set_stock(message.text)
    except ProductBuilderError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await _save_builder(state, builder)
    await state.set_state(AdminProductFSM.waiting_photo)
    await message.answer(
        "Шаг 5/5: пришли <b>фото</b> товара одним изображением.\n\nИли нажми «Без фото», и используется заглушка.",
        reply_markup=AdminCatalogKeyboardFactory.skip_photo(),
    )


@router.message(AdminProductFSM.waiting_photo, F.photo)
async def add_product_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not message.photo:
        return
    builder = await _restore_builder(state)
    biggest = message.photo[-1]
    builder.set_image(biggest.file_id)
    await _finish_product(message, state, session, builder)


@router.callback_query(AdminProductFSM.waiting_photo, F.data == "adm_prod_skip_photo")
async def add_product_skip_photo(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    builder = await _restore_builder(state)
    builder.set_image(None)
    if isinstance(callback.message, Message):
        await _finish_product(callback.message, state, session, builder)
    await callback.answer()


async def _finish_product(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    builder: ProductBuilder,
) -> None:
    try:
        spec = builder.build()
    except ProductBuilderError as e:
        await message.answer(f"⚠️ {e}")
        await state.clear()
        return

    try:
        product = await AdminCatalogService(session).create_product(
            category_id=spec.category_id,
            name=spec.name,
            description=spec.description,
            price=spec.price,
            stock=spec.stock,
            image_file_id=spec.image_file_id,
        )
    except AdminCatalogError as e:
        await message.answer(f"⚠️ {e}")
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ Товар <b>{product.name}</b> добавлен.\nЦена: {product.price_rub:.2f}₽, остаток: {product.stock}."
    )


# ─── Утилиты ───────────────────────────────────────────────────


async def _restore_builder(state: FSMContext) -> ProductBuilder:
    """Восстанавливает Builder из FSM-state."""
    data = await state.get_data()
    builder = ProductBuilder(category_id=int(data["category_id"]))

    name = data.get("name")
    if isinstance(name, str):
        builder.name = name

    description = data.get("description")
    if isinstance(description, str):
        builder.description = description

    price = data.get("price")
    if isinstance(price, int):
        builder.price = price

    stock = data.get("stock")
    if isinstance(stock, int):
        builder.stock = stock

    image_file_id = data.get("image_file_id")
    if isinstance(image_file_id, str):
        builder.image_file_id = image_file_id

    return builder


async def _save_builder(state: FSMContext, builder: ProductBuilder) -> None:
    """Сохраняет состояние Builder в FSM-state."""
    await state.update_data(
        category_id=builder.category_id,
        name=builder.name,
        description=builder.description,
        price=builder.price,
        stock=builder.stock,
        image_file_id=builder.image_file_id,
    )


def _format_products_text(category, products: list) -> str:  # type: ignore[no-untyped-def, type-arg]
    if not products:
        return f"📋 Товары в <b>{category.name}</b>\n\nПока нет товаров."
    lines = [f"📋 Товары в <b>{category.name}</b>", ""]
    for p in products:
        marker = "" if p.is_active else " 🚫"
        lines.append(f"• <b>{p.name}</b>{marker} — {p.price_rub:.2f}₽, остаток: {p.stock}")
    return "\n".join(lines)


def _format_product_text(product) -> str:  # type: ignore[no-untyped-def]
    active = "активен" if product.is_active else "🚫 скрыт"
    return (
        f"<b>{product.name}</b>\n"
        f"Статус: {active}\n"
        f"Цена: <b>{product.price_rub:.2f}₽</b>\n"
        f"Остаток: <b>{product.stock}</b>\n\n"
        f"{product.description}"
    )
