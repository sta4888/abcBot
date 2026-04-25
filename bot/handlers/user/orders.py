import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.domain.order_states import get_order_state
from bot.keyboards.callbacks import (
    OrderCancelConfirmCallback,
    OrderCancelDismissCallback,
    OrderCancelRequestCallback,
    OrderPayCallback,
)
from bot.keyboards.user.main_menu import BTN_ORDERS
from bot.keyboards.user.orders import OrdersKeyboardFactory
from bot.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = Router(name="user.orders")


# ─── Я оплатил ────────────────────────────────────────────────────


@router.callback_query(OrderPayCallback.filter())
async def mark_order_paid(
    callback: CallbackQuery,
    callback_data: OrderPayCallback,
    session: AsyncSession,
) -> None:
    """'Я оплатил' — переход new → paid через стратегию + State."""
    if callback.from_user is None:
        await callback.answer()
        return

    order = await OrderService(session).confirm_payment(
        order_id=callback_data.order_id,
        user_id=callback.from_user.id,
    )
    if order is None:
        await callback.answer("Заказ не найден или уже оплачен", show_alert=True)
        return

    if isinstance(callback.message, Message):
        await callback.message.edit_text(f"⏳ Обрабатываем оплату заказа <b>#{order.id}</b>...")
    await callback.answer()


# ─── Мои заказы ───────────────────────────────────────────────────


@router.message(F.text == BTN_ORDERS)
async def show_my_orders(message: Message, session: AsyncSession) -> None:
    """Кнопка 'Мои заказы' в главном меню."""
    if message.from_user is None:
        return

    views = await OrderService(session).list_user_orders(message.from_user.id)
    if not views:
        await message.answer("У тебя пока нет заказов.")
        return

    text = _render_orders_text(views)
    kb = OrdersKeyboardFactory.my_orders_actions([(v.order.id, v.order.status) for v in views])
    await message.answer(text, reply_markup=kb)


# ─── Отмена заказа: запрос подтверждения ─────────────────────────


@router.callback_query(OrderCancelRequestCallback.filter())
async def cancel_request(
    callback: CallbackQuery,
    callback_data: OrderCancelRequestCallback,
    session: AsyncSession,
) -> None:
    """Запрос на отмену заказа — показываем диалог подтверждения."""
    if callback.from_user is None:
        await callback.answer()
        return

    # Проверим, что заказ ещё можно отменить (могло измениться, пока юзер думал)
    order_service = OrderService(session)
    views = await order_service.list_user_orders(callback.from_user.id)
    target = next(
        (v.order for v in views if v.order.id == callback_data.order_id),
        None,
    )
    if target is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    state = get_order_state(target.status)
    text = (
        f"❓ Точно отменить заказ <b>#{target.id}</b>?\n\n"
        f"Сумма: <b>{target.total / 100:.2f}₽</b>\n"
        f"Статус: {state.label}\n\n"
        f"Это действие нельзя отменить."
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text,
            reply_markup=OrdersKeyboardFactory.cancel_confirmation(target.id),
        )
    await callback.answer()


# ─── Отмена заказа: подтверждение ────────────────────────────────


@router.callback_query(OrderCancelConfirmCallback.filter())
async def cancel_confirm(
    callback: CallbackQuery,
    callback_data: OrderCancelConfirmCallback,
    session: AsyncSession,
) -> None:
    """Подтверждение отмены — выполняем переход через State."""
    if callback.from_user is None:
        await callback.answer()
        return

    order = await OrderService(session).cancel_order(
        order_id=callback_data.order_id,
        user_id=callback.from_user.id,
    )
    if order is None:
        await callback.answer(
            "Не получилось отменить (возможно, статус уже не позволяет)",
            show_alert=True,
        )
        return

    # Сообщение об отмене пришлёт UserNotifierObserver. Здесь только закрываем экран.
    if isinstance(callback.message, Message):
        await callback.message.edit_text(f"⏳ Отменяем заказ <b>#{order.id}</b>...")
    await callback.answer()


# ─── Отмена заказа: отказ от отмены ──────────────────────────────


@router.callback_query(OrderCancelDismissCallback.filter())
async def cancel_dismiss(callback: CallbackQuery, session: AsyncSession) -> None:
    """'Нет, оставить' — возвращаемся к списку заказов."""
    if callback.from_user is None:
        await callback.answer()
        return

    views = await OrderService(session).list_user_orders(callback.from_user.id)
    if not views:
        if isinstance(callback.message, Message):
            await callback.message.edit_text("У тебя пока нет заказов.")
        await callback.answer()
        return

    text = _render_orders_text(views)
    kb = OrdersKeyboardFactory.my_orders_actions([(v.order.id, v.order.status) for v in views])
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Утилита ──────────────────────────────────────────────────────


def _render_orders_text(views: list) -> str:  # type: ignore[type-arg]
    """Текст экрана 'Мои заказы'."""
    lines: list[str] = ["📦 <b>Твои заказы</b>", ""]
    for v in views:
        order = v.order
        state = get_order_state(order.status)
        lines.append(
            f"<b>#{order.id}</b> — {state.label}\n"
            f"  Сумма: {order.total / 100:.2f}₽, "
            f"товаров: {v.items_count}\n"
            f"  Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
    return "\n\n".join(lines)
