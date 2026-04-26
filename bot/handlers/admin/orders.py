import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.domain.order_states import get_order_state
from bot.filters.admin import AdminFilter
from bot.keyboards.admin.main_menu import ADMIN_BTN_ORDERS
from bot.keyboards.admin.orders import AdminOrdersKeyboardFactory
from bot.keyboards.callbacks import (
    AdminOrderActionCallback,
    AdminOrdersListCallback,
    AdminOrderViewCallback,
)
from bot.services.admin_order_service import AdminOrderService
from bot.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = Router(name="admin.orders")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


# ─── Список заказов ─────────────────────────────────────────────


@router.message(F.text == ADMIN_BTN_ORDERS)
async def show_orders_from_menu(message: Message, session: AsyncSession) -> None:
    """Кнопка '📦 Заказы' в админ-меню."""
    orders = await AdminOrderService(session).list_orders(statuses=None)
    text = _format_orders_list(orders, current_filter="")
    kb = AdminOrdersKeyboardFactory.orders_list(orders, current_filter="")
    await message.answer(text, reply_markup=kb)


@router.callback_query(AdminOrdersListCallback.filter())
async def show_orders_filtered(
    callback: CallbackQuery,
    callback_data: AdminOrdersListCallback,
    session: AsyncSession,
) -> None:
    """Применение фильтра в списке заказов."""
    statuses = None if callback_data.status == "" else (callback_data.status,)

    orders = await AdminOrderService(session).list_orders(statuses=statuses)
    text = _format_orders_list(orders, current_filter=callback_data.status)
    kb = AdminOrdersKeyboardFactory.orders_list(orders, current_filter=callback_data.status)
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Карточка заказа ────────────────────────────────────────────


@router.callback_query(AdminOrderViewCallback.filter())
async def show_order_card(
    callback: CallbackQuery,
    callback_data: AdminOrderViewCallback,
    session: AsyncSession,
) -> None:
    order = await AdminOrderService(session).get_order(callback_data.order_id)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    text = _format_order_card(order)
    kb = AdminOrdersKeyboardFactory.order_card(order)
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Действие над заказом ──────────────────────────────────────


@router.callback_query(AdminOrderActionCallback.filter())
async def apply_order_action(
    callback: CallbackQuery,
    callback_data: AdminOrderActionCallback,
    session: AsyncSession,
) -> None:
    """Применить ship/deliver/cancel — переход через State + Observer."""
    order_service = OrderService(session)
    action = callback_data.action

    if action == "ship":
        order = await order_service.ship_order(callback_data.order_id)
    elif action == "deliver":
        order = await order_service.deliver_order(callback_data.order_id)
    elif action == "cancel":
        # cancel_order требует user_id (для проверки владения).
        # Админу нужно отменять любой — обходим через прямой переход.
        # Это допустимо: админ имеет привилегию.
        order = await _admin_cancel_order(order_service, callback_data.order_id)
    else:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    if order is None:
        await callback.answer(
            "Не получилось — переход не разрешён в текущем статусе",
            show_alert=True,
        )
        return

    # Перерисовать карточку
    text = _format_order_card(order)
    kb = AdminOrdersKeyboardFactory.order_card(order)
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer(f"Статус: {get_order_state(order.status).label}")


async def _admin_cancel_order(order_service: OrderService, order_id: int):  # type: ignore[no-untyped-def]
    """Админская отмена: без проверки владельца.

    Прямой вызов внутреннего _apply_transition. Это намеренный обход:
    у админа есть полномочие отменять любой заказ.
    """
    order = await order_service._order_repo.get_by_id(order_id)
    if order is None:
        return None
    return await order_service._apply_transition(order, action="cancel")


# ─── Утилиты ───────────────────────────────────────────────────


def _format_orders_list(orders: list, current_filter: str) -> str:  # type: ignore[type-arg]
    if not orders:
        if current_filter == "":
            return "📦 Заказы\n\nАктивных заказов нет."
        state = get_order_state(current_filter)
        return f"📦 Заказы\n\nНет заказов в статусе {state.label}."
    return f"📦 <b>Заказы</b> ({len(orders)})"


def _format_order_card(order) -> str:  # type: ignore[no-untyped-def]
    state = get_order_state(order.status)
    items_lines = "\n".join(f"  • {it.product_name} × {it.quantity} = {it.line_total / 100:.2f}₽" for it in order.items)
    return (
        f"📦 <b>Заказ #{order.id}</b>\n\n"
        f"Статус: {state.label}\n"
        f"Сумма: <b>{order.total / 100:.2f}₽</b>\n"
        f"Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Состав:</b>\n{items_lines}\n\n"
        f"<b>Доставка:</b> {order.delivery_method}\n"
        f"<b>Адрес:</b> <code>{order.delivery_address}</code>\n"
        f"<b>Телефон:</b> <code>{order.contact_phone}</code>\n"
        f"<b>Оплата:</b> {order.payment_method}" + (f"\n<b>Комментарий:</b> {order.comment}" if order.comment else "")
    )
