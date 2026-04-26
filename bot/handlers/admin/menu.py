import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.filters.admin import AdminFilter
from bot.keyboards.admin.main_menu import (
    ADMIN_BTN_CATEGORIES,
    ADMIN_BTN_EXIT,
    ADMIN_BTN_ORDERS,
    ADMIN_BTN_PRODUCTS,
    get_admin_menu,
)
from bot.keyboards.user.main_menu import get_main_menu

logger = logging.getLogger(__name__)

router = Router(name="admin.menu")
# Фильтр на весь роутер: только админ может им пользоваться
router.message.filter(AdminFilter())


# ─── Вход в админку ─────────────────────────────────────────────


@router.message(Command("admin"))
async def enter_admin(message: Message) -> None:
    """Команда /admin — вход в админ-панель."""
    if message.from_user is None:
        return
    logger.info("Admin entered: user_id=%d", message.from_user.id)
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\nВыбери раздел:",
        reply_markup=get_admin_menu(),
    )


# ─── Выход ───────────────────────────────────────────────────────


@router.message(F.text == ADMIN_BTN_EXIT)
async def exit_admin(message: Message) -> None:
    """Возврат в обычный режим."""
    await message.answer(
        "Возврат в магазин.",
        reply_markup=get_main_menu(),
    )


# ─── Заглушки разделов (наполним в этапах 2 и 3) ────────────────


@router.message(F.text == ADMIN_BTN_CATEGORIES)
async def categories_section(message: Message) -> None:
    await message.answer("📂 Раздел «Категории» появится в следующем этапе.")


@router.message(F.text == ADMIN_BTN_PRODUCTS)
async def products_section(message: Message) -> None:
    await message.answer("🛍 Раздел «Товары» появится в следующем этапе.")


@router.message(F.text == ADMIN_BTN_ORDERS)
async def orders_section(message: Message) -> None:
    await message.answer("📦 Раздел «Заказы» появится в финальном этапе.")
