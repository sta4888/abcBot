import logging

from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.callbacks import AddToCartCallback
from bot.services.cart_service import CartService

logger = logging.getLogger(__name__)

router = Router(name="user.cart")


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

    # Тост над кнопкой — не меняем сам экран
    await callback.answer(text, show_alert=False)
