import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.callbacks import (
    CheckoutCancelCallback,
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
from bot.services.cart_service import CartService
from bot.services.order_builder import (
    InvalidFieldError,
    OrderBuilder,
    OrderItemSpec,
)
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
    """Переход на шаг подтверждения. Полная реализация — в этапе 3."""
    await state.set_state(CheckoutState.waiting_confirmation)
    await message.answer(
        "✅ Все данные собраны.\n\n"
        "Шаг подтверждения и финальное оформление появятся в следующем этапе.\n"
        f"Сейчас в билдере:\n"
        f"• Адрес: <code>{builder.address}</code>\n"
        f"• Доставка: <code>{builder.delivery_method}</code>\n"
        f"• Телефон: <code>{builder.phone}</code>\n"
        f"• Оплата: <code>{builder.payment_method}</code>\n"
        f"• Комментарий: <code>{builder.comment or '—'}</code>\n"
        f"• Итого: <b>{builder.total / 100:.2f}₽</b>"
    )


# ─── Отмена ────────────────────────────────────────────────────────


@router.callback_query(CheckoutCancelCallback.filter())
async def cancel_checkout(callback: CallbackQuery, state: FSMContext) -> None:
    """Сброс FSM — выход из оформления."""
    await state.clear()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("❌ Оформление отменено. Корзина сохранена.")
    await callback.answer()
