import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.domain.order_states import get_order_state
from bot.keyboards.callbacks import OrderPayCallback
from bot.keyboards.user.main_menu import BTN_ORDERS
from bot.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = Router(name="user.orders")


# ─── Я оплатил (заглушечная оплата) ──────────────────────────────


@router.callback_query(OrderPayCallback.filter())
async def mark_order_paid(
    callback: CallbackQuery,
    callback_data: OrderPayCallback,
    session: AsyncSession,
) -> None:
    """'Я оплатил' — переход new → paid через стратегию + State.

    Сообщение об успехе шлёт UserNotifierObserver через EventBus.
    Здесь только обновляем экран — убираем кнопку 'Я оплатил'.
    """
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

    # Просто обновим экран этого сообщения, чтобы пользователь видел
    # что кнопки больше нет. Реальное уведомление прилетит отдельно от Observer.
    if isinstance(callback.message, Message):
        await callback.message.edit_text(f"⏳ Обрабатываем оплату заказа <b>#{order.id}</b>...")
    await callback.answer()


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
            f"<b>#{order.id}</b> — {get_order_state(order.status).label}\n"
            f"  Сумма: {order.total / 100:.2f}₽, "
            f"товаров: {v.items_count}\n"
            f"  Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

    await message.answer("\n\n".join(lines))
