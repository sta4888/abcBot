from aiogram.filters.callback_data import CallbackData


class CategoryCallback(CallbackData, prefix="cat"):
    """Нажатие на категорию — открыть её страницу товаров.

    page: индекс страницы (с 0). При нажатии на категорию из списка — 0.
    При пагинации — 1, 2, и т.д.
    """

    category_id: int
    page: int = 0


class ProductCallback(CallbackData, prefix="prod"):
    """Нажатие на товар в списке."""

    product_id: int


class CatalogBackCallback(CallbackData, prefix="cat_back"):
    """Кнопка 'назад' — возврат к списку категорий."""
