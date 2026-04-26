import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin.catalog import AdminCatalogKeyboardFactory
from bot.keyboards.admin.main_menu import ADMIN_BTN_CATEGORIES
from bot.keyboards.callbacks import (
    AdminCancelCallback,
    AdminCategoriesShowCallback,
    AdminCategoryAddCallback,
    AdminCategoryEditCallback,
    AdminCategoryRenameCallback,
    AdminCategoryToggleCallback,
)
from bot.services.admin_catalog_service import (
    AdminCatalogError,
    AdminCatalogService,
)
from bot.states.admin import AdminCategoryFSM, AdminCategoryRenameFSM

logger = logging.getLogger(__name__)

router = Router(name="admin.categories")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


# ─── Список категорий ───────────────────────────────────────────


@router.message(F.text == ADMIN_BTN_CATEGORIES)
async def show_categories(message: Message, session: AsyncSession) -> None:
    """Кнопка '📂 Категории' в админ-меню."""
    cats = await AdminCatalogService(session).list_all_categories()
    text = _format_categories_text(cats)
    kb = AdminCatalogKeyboardFactory.categories_list(cats)
    await message.answer(text, reply_markup=kb)


@router.callback_query(AdminCategoriesShowCallback.filter())
async def show_categories_cb(callback: CallbackQuery, session: AsyncSession) -> None:
    """Перерисовать список — после действий."""
    cats = await AdminCatalogService(session).list_all_categories()
    text = _format_categories_text(cats)
    kb = AdminCatalogKeyboardFactory.categories_list(cats)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Карточка категории ─────────────────────────────────────────


@router.callback_query(AdminCategoryEditCallback.filter())
async def show_category_card(
    callback: CallbackQuery,
    callback_data: AdminCategoryEditCallback,
    session: AsyncSession,
) -> None:
    cat = await AdminCatalogService(session).get_category(callback_data.category_id)
    if cat is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    active_label = "✅ активна" if cat.is_active else "🚫 скрыта"
    text = f"<b>{cat.name}</b>\nСтатус: {active_label}\nОписание: {cat.description or '—'}"
    kb = AdminCatalogKeyboardFactory.category_card(cat)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Toggle ─────────────────────────────────────────────────────


@router.callback_query(AdminCategoryToggleCallback.filter())
async def toggle_category(
    callback: CallbackQuery,
    callback_data: AdminCategoryToggleCallback,
    session: AsyncSession,
) -> None:
    cat = await AdminCatalogService(session).toggle_category_active(callback_data.category_id)
    if cat is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    # Перерисовать карточку
    active_label = "✅ активна" if cat.is_active else "🚫 скрыта"
    text = f"<b>{cat.name}</b>\nСтатус: {active_label}\nОписание: {cat.description or '—'}"
    kb = AdminCatalogKeyboardFactory.category_card(cat)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Категория скрыта" if not cat.is_active else "Категория показана")


# ─── Добавление категории (FSM) ────────────────────────────────


@router.callback_query(AdminCategoryAddCallback.filter())
async def add_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminCategoryFSM.waiting_name)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "✏️ Введи имя новой категории (например: «Аксессуары»):",
            reply_markup=AdminCatalogKeyboardFactory.cancel_only(),
        )
    await callback.answer()


@router.message(AdminCategoryFSM.waiting_name, F.text)
async def add_category_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.text is None:
        return
    try:
        await AdminCatalogService(session).create_category(name=message.text, description=None)
    except AdminCatalogError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await state.clear()
    cats = await AdminCatalogService(session).list_all_categories()
    await message.answer(
        f"✅ Категория добавлена.\n\n{_format_categories_text(cats)}",
        reply_markup=AdminCatalogKeyboardFactory.categories_list(cats),
    )


# ─── Переименование (FSM) ──────────────────────────────────────


@router.callback_query(AdminCategoryRenameCallback.filter())
async def rename_category_start(
    callback: CallbackQuery,
    callback_data: AdminCategoryRenameCallback,
    state: FSMContext,
) -> None:
    await state.set_state(AdminCategoryRenameFSM.waiting_name)
    await state.update_data(category_id=callback_data.category_id)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "✏️ Введи новое имя категории:",
            reply_markup=AdminCatalogKeyboardFactory.cancel_only(),
        )
    await callback.answer()


@router.message(AdminCategoryRenameFSM.waiting_name, F.text)
async def rename_category_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.text is None:
        return
    data = await state.get_data()
    category_id = int(data["category_id"])

    try:
        result = await AdminCatalogService(session).rename_category(category_id, message.text)
    except AdminCatalogError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await state.clear()
    if result is None:
        await message.answer("Категория не найдена.")
        return

    await message.answer(
        f"✅ Переименовано в <b>{result.name}</b>.",
    )


# ─── Отмена ─────────────────────────────────────────────────────


@router.callback_query(AdminCancelCallback.filter())
async def cancel_admin_fsm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()


# ─── Утилита ────────────────────────────────────────────────────


def _format_categories_text(cats: list) -> str:  # type: ignore[type-arg]
    if not cats:
        return "📂 <b>Категории</b>\n\nПока нет ни одной категории."
    lines = ["📂 <b>Категории</b>", ""]
    for c in cats:
        marker = "" if c.is_active else " 🚫"
        lines.append(f"• <b>{c.name}</b>{marker}")
    return "\n".join(lines)
