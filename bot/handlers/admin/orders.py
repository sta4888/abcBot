import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = Router(name="admin.orders")
# Защита всего роутера: только админ может использовать команды
router.message.filter(AdminFilter())


@router.message(Command("admin_ship"))
async def admin_ship(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    """Перевести заказ в статус 'shipped'. Использование: /admin_ship 42"""
    order_id = _parse_order_id(command)
    if order_id is None:
        await message.answer("Использование: <code>/admin_ship &lt;order_id&gt;</code>")
        return

    order = await OrderService(session).ship_order(order_id)
    if order is None:
        await message.answer(f"❌ Не удалось отправить заказ #{order_id} (не найден или статус не позволяет).")
        return

    await message.answer(f"✅ Заказ #{order.id} отправлен.")


@router.message(Command("admin_deliver"))
async def admin_deliver(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    """Перевести заказ в статус 'delivered'. Использование: /admin_deliver 42"""
    order_id = _parse_order_id(command)
    if order_id is None:
        await message.answer("Использование: <code>/admin_deliver &lt;order_id&gt;</code>")
        return

    order = await OrderService(session).deliver_order(order_id)
    if order is None:
        await message.answer(f"❌ Не удалось пометить заказ #{order_id} как доставленный.")
        return

    await message.answer(f"✅ Заказ #{order.id} доставлен.")


def _parse_order_id(command: CommandObject) -> int | None:
    """Извлекает order_id из аргументов команды."""
    if command.args is None:
        return None
    try:
        return int(command.args.strip())
    except ValueError:
        return None
