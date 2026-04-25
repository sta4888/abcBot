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


class ProductCardCallback(CallbackData, prefix="prod_card"):
    """Открыть карточку товара в режиме карточного просмотра.

    page = индекс товара в категории (с 0).
    """

    category_id: int
    page: int


class ProductsListModeCallback(CallbackData, prefix="prod_list"):
    """Переключиться на режим списка для категории."""

    category_id: int


class CheckoutDeliveryCallback(CallbackData, prefix="ck_dlv"):
    """Выбор способа доставки в FSM."""

    method: str  # 'courier' | 'pickup' | 'post'


class CheckoutPaymentCallback(CallbackData, prefix="ck_pay"):
    """Выбор способа оплаты в FSM."""

    method: str  # 'fake' пока что


class CheckoutSkipCommentCallback(CallbackData, prefix="ck_skip_cmt"):
    """Пропустить ввод комментария."""


class CheckoutCancelCallback(CallbackData, prefix="ck_cancel"):
    """Отменить процесс оформления и выйти из FSM."""


class CheckoutConfirmCallback(CallbackData, prefix="ck_confirm"):
    """Подтвердить заказ — финальный шаг FSM."""


class OrderPayCallback(CallbackData, prefix="order_pay"):
    """'Я оплатил' для конкретного заказа (заглушечная оплата)."""

    order_id: int
