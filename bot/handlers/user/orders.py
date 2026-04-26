import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.domain.order_states import get_order_state
from bot.keyboards.callbacks import (
    OrderCancelConfirmCallback,
    OrderCancelDismissCallback,
    OrderCancelRequestCallback,
    OrderPayCallback,
    UserOrdersListCallback,
    UserOrderViewCallback,
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
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(f"⏳ Обрабатываем оплату заказа <b>#{order.id}</b>...")
    await callback.answer()


# ─── Список заказов ───────────────────────────────────────────────


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
    kb = OrdersKeyboardFactory.my_orders_list(views)
    await message.answer(text, reply_markup=kb)


@router.callback_query(UserOrdersListCallback.filter())
async def back_to_orders_list(callback: CallbackQuery, session: AsyncSession) -> None:
    """Возврат к списку из карточки заказа."""
    if callback.from_user is None:
        await callback.answer()
        return

    views = await OrderService(session).list_user_orders(callback.from_user.id)
    if not views:
        if isinstance(callback.message, Message):
            with suppress(TelegramBadRequest):
                await callback.message.edit_text("У тебя пока нет заказов.")
        await callback.answer()
        return

    text = _render_orders_text(views)
    kb = OrdersKeyboardFactory.my_orders_list(views)
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Карточка заказа ─────────────────────────────────────────────


@router.callback_query(UserOrderViewCallback.filter())
async def show_order_card(
    callback: CallbackQuery,
    callback_data: UserOrderViewCallback,
    session: AsyncSession,
) -> None:
    """Открыть карточку заказа пользователя.

    Загружаем все заказы и фильтруем — это безопаснее, чем дёргать get_by_id
    напрямую, потому что мы автоматически проверяем владение.
    """
    if callback.from_user is None:
        await callback.answer()
        return

    views = await OrderService(session).list_user_orders(callback.from_user.id)
    target = next(
        (v.order for v in views if v.order.id == callback_data.order_id),
        None,
    )
    if target is None:
        await callback.answer(
            "Заказ не найден или принадлежит другому пользователю",
            show_alert=True,
        )
        return

    text = _format_order_card(target)
    kb = OrdersKeyboardFactory.order_card(target)
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Отмена заказа: запрос подтверждения ─────────────────────────


@router.callback_query(OrderCancelRequestCallback.filter())
async def cancel_request(
    callback: CallbackQuery,
    callback_data: OrderCancelRequestCallback,
    session: AsyncSession,
) -> None:
    """Запрос на отмену — диалог подтверждения."""
    if callback.from_user is None:
        await callback.answer()
        return

    views = await OrderService(session).list_user_orders(callback.from_user.id)
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
        with suppress(TelegramBadRequest):
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
            "Не получилось отменить (статус уже не позволяет)",
            show_alert=True,
        )
        return

    # Уведомление об отмене пришлёт UserNotifierObserver
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(f"⏳ Отменяем заказ <b>#{order.id}</b>...")
    await callback.answer()


# ─── Отмена заказа: отказ от отмены ──────────────────────────────


@router.callback_query(OrderCancelDismissCallback.filter())
async def cancel_dismiss(callback: CallbackQuery, session: AsyncSession) -> None:
    """'Нет, оставить' — возвращаемся к списку заказов."""
    await back_to_orders_list(callback, session)


# ─── Утилиты ─────────────────────────────────────────────────────


def _render_orders_text(views: list) -> str:  # type: ignore[type-arg]
    """Шапка экрана 'Мои заказы'."""
    return f"📦 <b>Твои заказы</b> ({len(views)})\n\nНажми на заказ, чтобы посмотреть детали."


def _format_order_card(order) -> str:  # type: ignore[no-untyped-def]
    """Полная карточка заказа со составом."""
    state = get_order_state(order.status)

    items_lines: list[str] = []
    for it in order.items:
        items_lines.append(f"  • {it.product_name} × {it.quantity} = {it.line_total / 100:.2f}₽")
    items_block = "\n".join(items_lines) or "  (состав не сохранён)"

    delivery_labels = {
        "courier": "🚚 Курьером",
        "pickup": "🏬 Самовывоз",
        "post": "📮 Почтой",
    }
    delivery_label = delivery_labels.get(order.delivery_method, order.delivery_method)

    payment_labels = {
        "fake": "🧪 Тестовая",
        "yookassa": "💳 ЮKassa",
    }
    payment_label = payment_labels.get(order.payment_method, order.payment_method)

    parts = [
        f"📦 <b>Заказ #{order.id}</b>",
        f"Статус: {state.label}",
        f"Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}",
        "",
        "<b>Состав:</b>",
        items_block,
        "",
        f"<b>Сумма:</b> {order.total / 100:.2f}₽",
        f"<b>Доставка:</b> {delivery_label}",
        f"<b>Адрес:</b> <code>{order.delivery_address}</code>",
        f"<b>Телефон:</b> <code>{order.contact_phone}</code>",
        f"<b>Оплата:</b> {payment_label}",
    ]
    if order.comment:
        parts.append(f"<b>Комментарий:</b> {order.comment}")

    return "\n".join(parts)
