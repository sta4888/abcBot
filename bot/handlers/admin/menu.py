import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.filters.admin import AdminFilter
from bot.keyboards.admin.main_menu import (
    ADMIN_BTN_EXIT,
    ADMIN_BTN_ORDERS,
    get_admin_menu,
)
from bot.keyboards.user.main_menu import get_main_menu

logger = logging.getLogger(__name__)

router = Router(name="admin.menu")
router.message.filter(AdminFilter())


@router.message(Command("admin"))
async def enter_admin(message: Message) -> None:
    if message.from_user is None:
        return
    logger.info("Admin entered: user_id=%d", message.from_user.id)
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\nВыбери раздел:",
        reply_markup=get_admin_menu(),
    )


@router.message(F.text == ADMIN_BTN_EXIT)
async def exit_admin(message: Message) -> None:
    await message.answer("Возврат в магазин.", reply_markup=get_main_menu())


@router.message(F.text == ADMIN_BTN_ORDERS)
async def orders_section(message: Message) -> None:
    await message.answer("📦 Раздел «Заказы» появится в финальном этапе.")
