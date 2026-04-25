from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import (
    AddToCartCallback,
    CatalogBackCallback,
    CategoryCallback,
    ProductCallback,
)
from bot.models import Category, Product
from bot.utils.pagination import Page


class CatalogKeyboardFactory:
    """Фабрика клавиатур каталога — один источник истины для UI каталога."""

    @staticmethod
    def categories_list(categories: list[Category]) -> InlineKeyboardMarkup:
        """Список категорий — по одной в строке."""
        builder = InlineKeyboardBuilder()
        for cat in categories:
            builder.button(
                text=cat.name,
                callback_data=CategoryCallback(category_id=cat.id),
            )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def products_list(
        category_id: int,
        products_page: Page[Product],
    ) -> InlineKeyboardMarkup:
        """Список товаров с пагинацией."""
        builder = InlineKeyboardBuilder()

        # Сами товары — каждый своей строкой
        for prod in products_page.items:
            builder.button(
                text=f"{prod.name} — {prod.price_rub:.0f}₽",
                callback_data=ProductCallback(product_id=prod.id),
            )
        builder.adjust(1)

        # Ряд пагинации — если есть больше одной страницы
        if products_page.total_pages > 1:
            pagination_row: list[InlineKeyboardButton] = []

            if products_page.has_prev:
                pagination_row.append(
                    InlineKeyboardButton(
                        text="‹",
                        callback_data=CategoryCallback(
                            category_id=category_id,
                            page=products_page.page - 1,
                        ).pack(),
                    )
                )

            # Индикатор страницы — не кликабельный, просто информация.
            # callback_data="noop" — placeholder, хендлер на него не реагирует
            pagination_row.append(
                InlineKeyboardButton(
                    text=f"{products_page.page + 1}/{products_page.total_pages}",
                    callback_data="noop",
                )
            )

            if products_page.has_next:
                pagination_row.append(
                    InlineKeyboardButton(
                        text="›",
                        callback_data=CategoryCallback(
                            category_id=category_id,
                            page=products_page.page + 1,
                        ).pack(),
                    )
                )

            builder.row(*pagination_row)

        # Кнопка 'назад' к категориям — всегда последняя
        builder.row(
            InlineKeyboardButton(
                text="◀️ К категориям",
                callback_data=CatalogBackCallback().pack(),
            )
        )

        return builder.as_markup()

    @staticmethod
    def product_card(product: Product) -> InlineKeyboardMarkup:
        """Клавиатура карточки товара."""
        builder = InlineKeyboardBuilder()

        # Кнопка 'В корзину' — только если товар в наличии
        if product.is_in_stock:
            builder.row(
                InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data=AddToCartCallback(product_id=product.id).pack(),
                )
            )

        builder.row(
            InlineKeyboardButton(
                text="◀️ К товарам",
                callback_data=CategoryCallback(category_id=product.category_id).pack(),
            )
        )
        return builder.as_markup()
