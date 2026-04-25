from aiogram.filters.callback_data import CallbackData


class CategoryCallback(CallbackData, prefix="cat"):
    """Нажатие на категорию — открыть её страницу товаров."""

    category_id: int
    page: int = 0


class ProductCallback(CallbackData, prefix="prod"):
    """Нажатие на товар в списке."""

    product_id: int


class CatalogBackCallback(CallbackData, prefix="cat_back"):
    """Кнопка 'назад' — возврат к списку категорий."""


class AddToCartCallback(CallbackData, prefix="cart_add"):
    """Нажатие 'Добавить в корзину' на карточке товара."""

    product_id: int


class CartChangeQtyCallback(CallbackData, prefix="cart_qty"):
    """Изменить количество товара в корзине: delta = +1 или -1."""

    product_id: int
    delta: int


class CartRemoveCallback(CallbackData, prefix="cart_rm"):
    """Удалить товар из корзины."""

    product_id: int


class CartClearCallback(CallbackData, prefix="cart_clear"):
    """Очистить всю корзину."""


class CartShowCallback(CallbackData, prefix="cart_show"):
    """Показать корзину (используется при перезагрузке экрана)."""


class CheckoutStartCallback(CallbackData, prefix="checkout"):
    """Начать оформление заказа."""
