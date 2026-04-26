import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.callbacks import (
    CheckoutCancelCallback,
    CheckoutConfirmCallback,  # ← новый
    CheckoutDeliveryCallback,
    CheckoutPaymentCallback,
    CheckoutSkipCommentCallback,
    CheckoutStartCallback,
)
from bot.keyboards.user.checkout import (
    DELIVERY_LABELS,
    PAYMENT_LABELS,
    CheckoutKeyboardFactory,
)
from bot.keyboards.user.orders import OrdersKeyboardFactory  # ← новый
from bot.services.cart_service import CartService
from bot.services.order_builder import (
    InvalidFieldError,
    OrderBuilder,
    OrderItemSpec,
)
from bot.services.order_service import OrderService  # ← новый
from bot.states.checkout import CheckoutState

logger = logging.getLogger(__name__)

router = Router(name="user.checkout")


# ─── Старт оформления ───────────────────────────────────────────────


@router.callback_query(CheckoutStartCallback.filter())
async def start_checkout(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Пользователь нажал 'Оформить заказ' (с карточки или из корзины).

    Готовим OrderBuilder с позициями из корзины, кладём в FSM-state,
    переходим на первый шаг.
    """
    if callback.from_user is None:
        await callback.answer()
        return

    cart_summary = await CartService(session).get_summary(callback.from_user.id)
    if cart_summary.is_empty:
        await callback.answer("Корзина пуста — добавь товары", show_alert=True)
        return

    builder = OrderBuilder(user_id=callback.from_user.id)
    builder.set_items(
        [
            OrderItemSpec(
                product_id=line.product.id,
                product_name=line.product.name,
                price=line.product.price,
                quantity=line.quantity,
            )
            for line in cart_summary.lines
        ]
    )
    await state.set_data(builder.to_dict())
    await state.set_state(CheckoutState.waiting_address)

    text = (
        "📝 <b>Оформление заказа</b>\n\n"
        "Введи адрес доставки одним сообщением.\n"
        "Например: <i>г. Москва, ул. Ленина 12, кв. 34</i>"
    )
    await callback.message.answer(  # type: ignore[union-attr]
        text, reply_markup=CheckoutKeyboardFactory.cancel_only()
    )
    await callback.answer()


# ─── Шаг 1: адрес ──────────────────────────────────────────────────


@router.message(CheckoutState.waiting_address, F.text)
async def step_address(message: Message, state: FSMContext) -> None:
    """Получили адрес — валидируем, сохраняем, идём дальше."""
    if message.text is None:
        return

    data = await state.get_data()
    builder = OrderBuilder.from_dict(data)
    try:
        builder.set_address(message.text)
    except InvalidFieldError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await state.set_data(builder.to_dict())
    await state.set_state(CheckoutState.waiting_delivery)
    await message.answer(
        "🚚 Выбери способ доставки:",
        reply_markup=CheckoutKeyboardFactory.delivery_methods(),
    )


# ─── Шаг 2: доставка ──────────────────────────────────────────────


@router.callback_query(CheckoutState.waiting_delivery, CheckoutDeliveryCallback.filter())
async def step_delivery(
    callback: CallbackQuery,
    callback_data: CheckoutDeliveryCallback,
    state: FSMContext,
) -> None:
    """Выбран способ доставки."""
    data = await state.get_data()
    builder = OrderBuilder.from_dict(data)
    try:
        builder.set_delivery_method(callback_data.method)
    except InvalidFieldError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.set_data(builder.to_dict())
    await state.set_state(CheckoutState.waiting_phone)

    label = DELIVERY_LABELS.get(callback_data.method, callback_data.method)
    text = f"✅ Доставка: <b>{label}</b>\n\n📞 Введи контактный телефон.\nНапример: <code>+7 999 123 45 67</code>"
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=CheckoutKeyboardFactory.cancel_only())
    await callback.answer()


# ─── Шаг 3: телефон ───────────────────────────────────────────────


@router.message(CheckoutState.waiting_phone, F.text)
async def step_phone(message: Message, state: FSMContext) -> None:
    """Получили телефон — валидируем, идём к оплате."""
    if message.text is None:
        return

    data = await state.get_data()
    builder = OrderBuilder.from_dict(data)
    try:
        builder.set_phone(message.text)
    except InvalidFieldError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await state.set_data(builder.to_dict())
    await state.set_state(CheckoutState.waiting_payment)
    await message.answer(
        "💳 Выбери способ оплаты:",
        reply_markup=CheckoutKeyboardFactory.payment_methods(),
    )


# ─── Шаг 4: оплата ────────────────────────────────────────────────


@router.callback_query(CheckoutState.waiting_payment, CheckoutPaymentCallback.filter())
async def step_payment(
    callback: CallbackQuery,
    callback_data: CheckoutPaymentCallback,
    state: FSMContext,
) -> None:
    """Выбран способ оплаты."""
    data = await state.get_data()
    builder = OrderBuilder.from_dict(data)
    try:
        builder.set_payment_method(callback_data.method)
    except InvalidFieldError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.set_data(builder.to_dict())
    await state.set_state(CheckoutState.waiting_comment)

    label = PAYMENT_LABELS.get(callback_data.method, callback_data.method)
    text = (
        f"✅ Оплата: <b>{label}</b>\n\n"
        f"💬 Хочешь оставить комментарий к заказу?\n"
        f"Введи текст или нажми «Без комментария»."
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=CheckoutKeyboardFactory.comment_step())
    await callback.answer()


# ─── Шаг 5: комментарий ──────────────────────────────────────────


@router.message(CheckoutState.waiting_comment, F.text)
async def step_comment_text(message: Message, state: FSMContext) -> None:
    """Получили комментарий текстом."""
    if message.text is None:
        return

    data = await state.get_data()
    builder = OrderBuilder.from_dict(data)
    try:
        builder.set_comment(message.text)
    except InvalidFieldError as e:
        await message.answer(f"⚠️ {e}\n\nПопробуй ещё раз.")
        return

    await state.set_data(builder.to_dict())
    await _go_to_confirmation(message, state, builder)


@router.callback_query(CheckoutState.waiting_comment, CheckoutSkipCommentCallback.filter())
async def step_comment_skip(callback: CallbackQuery, state: FSMContext) -> None:
    """Пропустить комментарий."""
    data = await state.get_data()
    builder = OrderBuilder.from_dict(data)
    builder.set_comment(None)
    await state.set_data(builder.to_dict())
    if isinstance(callback.message, Message):
        await _go_to_confirmation(callback.message, state, builder)
    await callback.answer()


async def _go_to_confirmation(
    message: Message,
    state: FSMContext,
    builder: OrderBuilder,
) -> None:
    """Переход на шаг подтверждения: показать сводку и кнопки."""
    await state.set_state(CheckoutState.waiting_confirmation)
    await message.answer(
        builder.render_summary(),
        reply_markup=CheckoutKeyboardFactory.confirmation(),
    )


# ─── Шаг 6: подтверждение и создание заказа ────────────────────────


@router.callback_query(CheckoutState.waiting_confirmation, CheckoutConfirmCallback.filter())
async def confirm_checkout(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Подтверждение — создаём заказ в БД и сбрасываем FSM."""
    if callback.from_user is None:
        await callback.answer()
        return

    data = await state.get_data()
    builder = OrderBuilder.from_dict(data)

    # Финальная проверка: на всякий случай (вдруг что-то поломалось в FSM)
    if not builder.is_complete():
        await callback.answer("Не все поля заполнены", show_alert=True)
        await state.clear()
        return

    try:
        order = await OrderService(session).create_order_from_builder(builder)
    except Exception as e:
        logger.exception("Failed to create order")
        await callback.answer(f"Не удалось создать заказ: {e}", show_alert=True)
        await state.clear()
        return

    await state.clear()

    payment_init = await OrderService(session).initiate_payment(order)

    text = f"🎉 <b>Заказ #{order.id} создан!</b>\n\n{payment_init.text}"

    # Определяем клавиатуру по флагам стратегии:
    # - requires_user_action: кнопка "Я оплатил" (Fake)
    # - payment_url: кнопка "Оплатить" с переходом по URL (YooKassa)
    # - ничего: пользователь просто ждёт (на случай провайдеров без UI)
    kb = None
    if payment_init.requires_user_action:
        kb = OrdersKeyboardFactory.pay_action(order.id)
    elif payment_init.payment_url is not None:
        kb = OrdersKeyboardFactory.payment_url_action(payment_init.payment_url)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── Отмена ────────────────────────────────────────────────────────


@router.callback_query(CheckoutCancelCallback.filter())
async def cancel_checkout(callback: CallbackQuery, state: FSMContext) -> None:
    """Сброс FSM — выход из оформления."""
    await state.clear()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("❌ Оформление отменено. Корзина сохранена.")
    await callback.answer()
