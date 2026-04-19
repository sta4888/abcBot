from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import (
    CatalogBackCallback,
    CategoryCallback,
    ProductCallback,
)
from bot.models import Category, Product


class CatalogKeyboardFactory:
    """Фабрика клавиатур каталога.

    Каждый метод — это отдельный Factory Method для конкретного экрана.
    Все они возвращают готовый InlineKeyboardMarkup, который хендлер прикрепляет к сообщению.
    """

    @staticmethod
    def categories_list(categories: list[Category]) -> InlineKeyboardMarkup:
        """Клавиатура со списком категорий — по одной в строке."""
        builder = InlineKeyboardBuilder()
        for cat in categories:
            builder.button(
                text=cat.name,
                callback_data=CategoryCallback(category_id=cat.id),
            )
        builder.adjust(1)  # по одной кнопке в ряду
        return builder.as_markup()

    @staticmethod
    def products_list(
        products: list[Product],
        show_back_button: bool = True,
    ) -> InlineKeyboardMarkup:
        """Клавиатура со списком товаров в категории."""
        builder = InlineKeyboardBuilder()
        for prod in products:
            builder.button(
                text=f"{prod.name} — {prod.price_rub:.0f}₽",
                callback_data=ProductCallback(product_id=prod.id),
            )
        builder.adjust(1)

        if show_back_button:
            builder.row(
                InlineKeyboardButton(
                    text="◀️ К категориям",
                    callback_data=CatalogBackCallback().pack(),
                )
            )

        return builder.as_markup()

    @staticmethod
    def product_card(product: Product) -> InlineKeyboardMarkup:
        """Клавиатура под карточкой товара.

        Пока только 'Назад', позже сюда добавим 'В корзину', '+/-', и т.п.
        """
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="◀️ К товарам",
                callback_data=CategoryCallback(category_id=product.category_id).pack(),
            )
        )
        return builder.as_markup()
