import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.callbacks import OrderPayCallback
from bot.keyboards.user.main_menu import BTN_ORDERS
from bot.services.order_service import STATUS_LABELS, OrderService

logger = logging.getLogger(__name__)

router = Router(name="user.orders")


# ─── Я оплатил (заглушечная оплата) ──────────────────────────────


@router.callback_query(OrderPayCallback.filter())
async def mark_order_paid(
    callback: CallbackQuery,
    callback_data: OrderPayCallback,
    session: AsyncSession,
) -> None:
    """'Я оплатил' — заглушечный переход new → paid."""
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

    text = (
        f"✅ <b>Заказ #{order.id} оплачен</b>\n\n"
        f"Сумма: <b>{order.total / 100:.2f}₽</b>\n"
        f"Статус: {STATUS_LABELS[order.status]}\n\n"
        f"Спасибо! Скоро мы займёмся твоим заказом."
    )

    if isinstance(callback.message, Message):
        # Убираем клавиатуру оплаты — больше нечего нажимать
        await callback.message.edit_text(text)
    await callback.answer("Оплата принята")


# ─── Мои заказы ──────────────────────────────────────────────────


@router.message(F.text == BTN_ORDERS)
async def show_my_orders(message: Message, session: AsyncSession) -> None:
    """Кнопка 'Мои заказы' в главном меню."""
    if message.from_user is None:
        return

    views = await OrderService(session).list_user_orders(message.from_user.id)
    if not views:
        await message.answer("У тебя пока нет заказов.")
        return

    lines: list[str] = ["📦 <b>Твои заказы</b>", ""]
    for v in views:
        order = v.order
        lines.append(
            f"<b>#{order.id}</b> — {STATUS_LABELS.get(order.status, order.status)}\n"
            f"  Сумма: {order.total / 100:.2f}₽, "
            f"товаров: {v.items_count}\n"
            f"  Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

    await message.answer("\n\n".join(lines))
