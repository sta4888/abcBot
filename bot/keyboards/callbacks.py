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


class OrderCancelRequestCallback(CallbackData, prefix="ord_cancel_q"):
    """Запрос на отмену заказа — показать диалог подтверждения."""

    order_id: int


class OrderCancelConfirmCallback(CallbackData, prefix="ord_cancel_y"):
    """Подтверждение отмены заказа."""

    order_id: int


class OrderCancelDismissCallback(CallbackData, prefix="ord_cancel_n"):
    """Отказ от отмены — вернуться к списку заказов."""


# ─── Admin: categories ────────────────────────────────────────


class AdminCategoriesShowCallback(CallbackData, prefix="adm_cats"):
    """Открыть/перерисовать список категорий."""


class AdminCategoryEditCallback(CallbackData, prefix="adm_cat_e"):
    """Открыть карточку категории для редактирования."""

    category_id: int


class AdminCategoryAddCallback(CallbackData, prefix="adm_cat_add"):
    """Запустить FSM добавления категории."""


class AdminCategoryRenameCallback(CallbackData, prefix="adm_cat_rn"):
    """Запустить FSM переименования категории."""

    category_id: int


class AdminCategoryToggleCallback(CallbackData, prefix="adm_cat_tg"):
    """Переключить is_active у категории."""

    category_id: int


# ─── Admin: products ──────────────────────────────────────────


class AdminProductsShowCallback(CallbackData, prefix="adm_prods"):
    """Открыть список товаров категории."""

    category_id: int


class AdminProductEditCallback(CallbackData, prefix="adm_prod_e"):
    """Открыть карточку товара для редактирования."""

    product_id: int


class AdminProductAddCallback(CallbackData, prefix="adm_prod_add"):
    """Запустить FSM добавления товара в категорию."""

    category_id: int


class AdminProductToggleCallback(CallbackData, prefix="adm_prod_tg"):
    """Переключить is_active у товара."""

    product_id: int


class AdminProductStockCallback(CallbackData, prefix="adm_prod_st"):
    """Изменить остаток товара. delta: +1, +10, -1, -10."""

    product_id: int
    delta: int


class AdminCancelCallback(CallbackData, prefix="adm_cancel"):
    """Универсальная отмена FSM-сценария в админке."""


# ─── Admin: orders ────────────────────────────────────────────


class AdminOrdersListCallback(CallbackData, prefix="adm_ords"):
    """Список заказов с фильтром по статусу.

    status: пустая строка = все активные, иначе конкретный статус.
    """

    status: str = ""


class AdminOrderViewCallback(CallbackData, prefix="adm_ord_v"):
    """Открыть карточку заказа."""

    order_id: int


class AdminOrderActionCallback(CallbackData, prefix="adm_ord_a"):
    """Применить действие (ship/deliver/cancel) к заказу."""

    order_id: int
    action: str  # 'ship' | 'deliver' | 'cancel'


class CheckoutSkipPromoCallback(CallbackData, prefix="ck_skip_promo"):
    """Пропустить ввод промокода."""
