import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.callbacks import (
    AddToCartCallback,
    CartChangeQtyCallback,
    CartClearCallback,
    CartRemoveCallback,
    CartShowCallback,
    CheckoutStartCallback,
)
from bot.keyboards.user.cart import CartKeyboardFactory
from bot.keyboards.user.main_menu import BTN_CART
from bot.services.cart_service import CartService

logger = logging.getLogger(__name__)

router = Router(name="user.cart")


# ─── Добавление товара (с карточки товара) ──────────────────────────────


@router.callback_query(AddToCartCallback.filter())
async def add_to_cart(
    callback: CallbackQuery,
    callback_data: AddToCartCallback,
    session: AsyncSession,
) -> None:
    """Пользователь нажал 'В корзину' на карточке товара."""
    if callback.from_user is None:
        await callback.answer()
        return

    result = await CartService(session).add_item(
        user_id=callback.from_user.id,
        product_id=callback_data.product_id,
    )

    if result is None:
        await callback.answer("Товара нет в наличии", show_alert=True)
        return

    text = "✅ Товар добавлен в корзину" if result.is_new else f"➕ Количество в корзине: {result.item.quantity}"

    await callback.answer(text, show_alert=False)


# ─── Показ корзины ──────────────────────────────────────────────────────


@router.message(F.text == BTN_CART)
async def show_cart_from_menu(message: Message, session: AsyncSession) -> None:
    """Кнопка 'Корзина' в главном меню → присылаем экран корзины."""
    if message.from_user is None:
        return
    cart_service = CartService(session)
    summary = await cart_service.get_summary(message.from_user.id)
    text = cart_service.render_text(summary)
    kb = CartKeyboardFactory.cart_view(summary)
    await message.answer(text, reply_markup=kb)


@router.callback_query(CartShowCallback.filter())
async def show_cart_from_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Перезагрузка экрана корзины по callback (используется внутренне)."""
    if callback.from_user is None:
        await callback.answer()
        return
    await _refresh_cart_screen(callback, session)


# ─── Изменение количества ──────────────────────────────────────────────


@router.callback_query(CartChangeQtyCallback.filter())
async def change_quantity(
    callback: CallbackQuery,
    callback_data: CartChangeQtyCallback,
    session: AsyncSession,
) -> None:
    """Кнопка − или + рядом с товаром в корзине."""
    if callback.from_user is None:
        await callback.answer()
        return

    await CartService(session).change_quantity(
        user_id=callback.from_user.id,
        product_id=callback_data.product_id,
        delta=callback_data.delta,
    )
    await _refresh_cart_screen(callback, session)


# ─── Удаление позиции ──────────────────────────────────────────────────


@router.callback_query(CartRemoveCallback.filter())
async def remove_item(
    callback: CallbackQuery,
    callback_data: CartRemoveCallback,
    session: AsyncSession,
) -> None:
    """Кнопка 🗑 рядом с товаром."""
    if callback.from_user is None:
        await callback.answer()
        return

    removed = await CartService(session).remove_item(
        user_id=callback.from_user.id,
        product_id=callback_data.product_id,
    )
    if removed:
        await callback.answer("Товар удалён из корзины")
    await _refresh_cart_screen(callback, session)


# ─── Очистка ───────────────────────────────────────────────────────────


@router.callback_query(CartClearCallback.filter())
async def clear_cart(callback: CallbackQuery, session: AsyncSession) -> None:
    """Кнопка 'Очистить корзину'."""
    if callback.from_user is None:
        await callback.answer()
        return

    await CartService(session).clear(callback.from_user.id)
    await callback.answer("Корзина очищена")
    await _refresh_cart_screen(callback, session)


# ─── Оформление (заглушка до итерации 4) ───────────────────────────────


@router.callback_query(CheckoutStartCallback.filter())
async def start_checkout(callback: CallbackQuery, session: AsyncSession) -> None:
    """Заглушка — реальная FSM оформления появится в итерации 4."""
    if callback.from_user is None:
        await callback.answer()
        return

    summary = await CartService(session).get_summary(callback.from_user.id)
    if summary.is_empty:
        await callback.answer("Корзина пуста", show_alert=True)
        return

    await callback.answer(
        "Оформление заказа появится в следующих обновлениях 🛠",
        show_alert=True,
    )


# ─── Утилита ────────────────────────────────────────────────────────────


async def _refresh_cart_screen(callback: CallbackQuery, session: AsyncSession) -> None:
    """Обновляет экран корзины: подгружает свежий summary, перерисовывает.

    Вызывается после любого изменения корзины через callback'и.
    """
    if callback.from_user is None:
        return
    cart_service = CartService(session)
    summary = await cart_service.get_summary(callback.from_user.id)
    text = cart_service.render_text(summary)
    kb = CartKeyboardFactory.cart_view(summary)

    if isinstance(callback.message, Message):
        # Если корзина опустела — клавиатура есть, но без кнопок управления.
        # Это нормальное поведение, не ошибка.
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
