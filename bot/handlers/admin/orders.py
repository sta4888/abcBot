import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
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
from bot.services.commands import (
    AdminCancelOrderCommand,
    DeliverOrderCommand,
    ShipOrderCommand,
    get_command_history,
)
from bot.services.commands import (
    Command as OrderCommand,
)
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
    """Применить ship/deliver/cancel — через Command + History."""
    if callback.from_user is None:
        await callback.answer()
        return

    action = callback_data.action

    command: OrderCommand
    if action == "ship":
        command = ShipOrderCommand(
            order_id=callback_data.order_id,
            executor_user_id=callback.from_user.id,
        )
    elif action == "deliver":
        command = DeliverOrderCommand(
            order_id=callback_data.order_id,
            executor_user_id=callback.from_user.id,
        )
    elif action == "cancel":
        command = AdminCancelOrderCommand(
            order_id=callback_data.order_id,
            executor_user_id=callback.from_user.id,
        )
    else:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    # bind свежую сессию из middleware
    command.bind_session(session)

    success = await command.execute()
    if not success:
        await callback.answer(
            "Не получилось — переход не разрешён в текущем статусе",
            show_alert=True,
        )
        return

    get_command_history().push(command)

    order_service = OrderService(session)
    order = await order_service._order_repo.get_by_id(callback_data.order_id)
    if order is None:
        await callback.answer()
        return

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


# ─── Mock-webhook для YooKassa ────────────────────────────────


@router.message(Command("mock_pay"))
async def mock_yookassa_webhook(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    """Эмуляция webhook ЮKassa: 'пользователь оплатил инвойс'.

    В реальном проекте такой код живёт в HTTP-эндпоинте и вызывается
    провайдером. Здесь — админская команда для учебных целей.
    """
    if command.args is None:
        await message.answer("Использование: <code>/mock_pay &lt;order_id&gt;</code>")
        return

    try:
        order_id = int(command.args.strip())
    except ValueError:
        await message.answer("order_id должен быть числом.")
        return

    order_service = OrderService(session)
    order = await order_service._order_repo.get_by_id(order_id)
    if order is None:
        await message.answer(f"❌ Заказ #{order_id} не найден.")
        return

    if order.payment_method != "yookassa":
        await message.answer(
            f"⚠️ Заказ #{order_id} оплачивается через "
            f"<b>{order.payment_method}</b>, а не yookassa.\n"
            f"Команда /mock_pay только для yookassa."
        )
        return

    if order.status != "new":
        await message.answer(f"⚠️ Заказ #{order_id} уже не в статусе 'new' (текущий: {order.status}).")
        return

    # Шаг 1: эмулируем оплату на стороне SDK
    from bot.services.payment import get_payment_factory
    from bot.services.payment.yookassa_strategy import YooKassaPaymentStrategy

    strategy = get_payment_factory().get("yookassa")
    if not isinstance(strategy, YooKassaPaymentStrategy):
        await message.answer("❌ YooKassa-стратегия не зарегистрирована")
        return

    success = await strategy.simulate_webhook_payment(order_id)
    if not success:
        await message.answer("❌ Не удалось пометить инвойс оплаченным (возможно, инвойс не создан или уже оплачен).")
        return

    # Шаг 2: подтверждаем оплату через стандартный flow.
    # Это и есть webhook handler в учебной форме.
    confirmed = await order_service.confirm_payment(order_id=order_id, user_id=order.user_id)
    if confirmed is None:
        await message.answer("❌ Стратегия пометила оплату, но State не разрешил переход. Странно — посмотри логи.")
        return

    await message.answer(
        f"✅ Webhook эмулирован: заказ #{order_id} переведён в paid.\n"
        f"Пользователю отправлено уведомление через Observer."
    )


@router.message(Command("admin_undo"))
async def admin_undo_last(message: Message, session: AsyncSession) -> None:
    """Отменить последнее своё админское действие."""
    if message.from_user is None:
        return

    history = get_command_history()
    last = history.peek(message.from_user.id)
    if last is None:
        await message.answer("У тебя нет действий для отмены.\nСначала сделай что-нибудь через карточку заказа.")
        return

    command = history.pop(message.from_user.id)
    if command is None:
        return

    # Привязываем свежую сессию из текущего апдейта
    command.bind_session(session)

    success = await command.undo()
    if not success:
        await message.answer(
            f"❌ Не удалось откатить: <code>{command.summary}</code>\nВозможно, состояние заказа изменилось."
        )
        return

    await message.answer(f"↩️ Отменено: <code>{command.summary}</code>")
