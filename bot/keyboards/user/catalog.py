from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import (
    AddToCartCallback,
    CatalogBackCallback,
    CategoryCallback,
    ProductCallback,
    ProductCardCallback,
    ProductsListModeCallback,
)
from bot.models import Category, Product
from bot.services.catalog_service import CardView
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
        """Список товаров с пагинацией + кнопка переключения в режим карточек."""
        builder = InlineKeyboardBuilder()

        for prod in products_page.items:
            builder.button(
                text=f"{prod.name} — {prod.price_rub:.0f}₽",
                callback_data=ProductCallback(product_id=prod.id),
            )
        builder.adjust(1)

        # Ряд пагинации
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

        # Переключение в режим карточек (только если в категории есть товары)
        if products_page.total > 0:
            builder.row(
                InlineKeyboardButton(
                    text="🖼 Карточки с фото",
                    callback_data=ProductCardCallback(category_id=category_id, page=0).pack(),
                )
            )

        # Назад к категориям
        builder.row(
            InlineKeyboardButton(
                text="◀️ К категориям",
                callback_data=CatalogBackCallback().pack(),
            )
        )

        return builder.as_markup()

    @staticmethod
    def product_card(product: Product) -> InlineKeyboardMarkup:
        """Клавиатура старого детального экрана товара (открытого из списка)."""
        builder = InlineKeyboardBuilder()

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

    @staticmethod
    def product_slider_card(view: CardView) -> InlineKeyboardMarkup:
        """Клавиатура карточки в режиме слайдера: ‹ N/M › и [В корзину]."""
        builder = InlineKeyboardBuilder()

        # Кнопка 'В корзину' — только если в наличии
        if view.product.is_in_stock:
            builder.row(
                InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data=AddToCartCallback(product_id=view.product.id).pack(),
                )
            )

        # Ряд листания
        nav_row: list[InlineKeyboardButton] = []
        if view.has_prev:
            nav_row.append(
                InlineKeyboardButton(
                    text="‹",
                    callback_data=ProductCardCallback(category_id=view.category.id, page=view.page - 1).pack(),
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"{view.page + 1}/{view.total}",
                callback_data="noop",
            )
        )

        if view.has_next:
            nav_row.append(
                InlineKeyboardButton(
                    text="›",
                    callback_data=ProductCardCallback(category_id=view.category.id, page=view.page + 1).pack(),
                )
            )

        builder.row(*nav_row)

        # Переключение в список
        builder.row(
            InlineKeyboardButton(
                text="📋 Списком",
                callback_data=ProductsListModeCallback(category_id=view.category.id).pack(),
            )
        )

        # Назад к категориям
        builder.row(
            InlineKeyboardButton(
                text="◀️ К категориям",
                callback_data=CatalogBackCallback().pack(),
            )
        )

        return builder.as_markup()
