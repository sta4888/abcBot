from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import (
    AdminCancelCallback,
    AdminCategoriesShowCallback,
    AdminCategoryAddCallback,
    AdminCategoryEditCallback,
    AdminCategoryRenameCallback,
    AdminCategoryToggleCallback,
    AdminProductAddCallback,
    AdminProductEditCallback,
    AdminProductsShowCallback,
    AdminProductStockCallback,
    AdminProductToggleCallback,
)
from bot.models import Category, Product


class AdminCatalogKeyboardFactory:
    """Фабрика клавиатур админского каталога."""

    # ─── Categories ─────────────────────────────────────────────

    @staticmethod
    def categories_list(categories: list[Category]) -> InlineKeyboardMarkup:
        """Список всех категорий + кнопка добавления."""
        builder = InlineKeyboardBuilder()
        for cat in categories:
            badge = "" if cat.is_active else " 🚫"
            builder.button(
                text=f"{cat.name}{badge}",
                callback_data=AdminCategoryEditCallback(category_id=cat.id),
            )
        builder.adjust(1)
        builder.row(
            InlineKeyboardButton(
                text="➕ Добавить категорию",
                callback_data=AdminCategoryAddCallback().pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def category_card(category: Category) -> InlineKeyboardMarkup:
        """Карточка категории с действиями."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📋 Товары категории",
                callback_data=AdminProductsShowCallback(category_id=category.id).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✏️ Переименовать",
                callback_data=AdminCategoryRenameCallback(category_id=category.id).pack(),
            ),
            InlineKeyboardButton(
                text="🚫 Скрыть" if category.is_active else "✅ Показать",
                callback_data=AdminCategoryToggleCallback(category_id=category.id).pack(),
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="◀️ К категориям",
                callback_data=AdminCategoriesShowCallback().pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def cancel_only() -> InlineKeyboardMarkup:
        """Клавиатура с одной кнопкой отмены — для FSM."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=AdminCancelCallback().pack(),
            )
        )
        return builder.as_markup()

    # ─── Products ──────────────────────────────────────────────

    @staticmethod
    def products_list(category: Category, products: list[Product]) -> InlineKeyboardMarkup:
        """Список товаров + кнопка добавления."""
        builder = InlineKeyboardBuilder()
        for prod in products:
            stock_marker = "" if prod.stock > 0 else " ❗️"
            active_marker = "" if prod.is_active else " 🚫"
            builder.button(
                text=f"{prod.name} ({prod.price_rub:.0f}₽){stock_marker}{active_marker}",
                callback_data=AdminProductEditCallback(product_id=prod.id),
            )
        builder.adjust(1)
        builder.row(
            InlineKeyboardButton(
                text="➕ Добавить товар",
                callback_data=AdminProductAddCallback(category_id=category.id).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="◀️ К категории",
                callback_data=AdminCategoryEditCallback(category_id=category.id).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def product_card(product: Product) -> InlineKeyboardMarkup:
        """Карточка товара с действиями."""
        builder = InlineKeyboardBuilder()

        # Управление остатком: -10, -1, текущий, +1, +10
        builder.row(
            InlineKeyboardButton(
                text="−10",
                callback_data=AdminProductStockCallback(product_id=product.id, delta=-10).pack(),
            ),
            InlineKeyboardButton(
                text="−1",
                callback_data=AdminProductStockCallback(product_id=product.id, delta=-1).pack(),
            ),
            InlineKeyboardButton(
                text=f"📦 {product.stock}",
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text="+1",
                callback_data=AdminProductStockCallback(product_id=product.id, delta=1).pack(),
            ),
            InlineKeyboardButton(
                text="+10",
                callback_data=AdminProductStockCallback(product_id=product.id, delta=10).pack(),
            ),
        )

        builder.row(
            InlineKeyboardButton(
                text="🚫 Скрыть" if product.is_active else "✅ Показать",
                callback_data=AdminProductToggleCallback(product_id=product.id).pack(),
            )
        )

        builder.row(
            InlineKeyboardButton(
                text="◀️ К товарам",
                callback_data=AdminProductsShowCallback(category_id=product.category_id).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def skip_photo() -> InlineKeyboardMarkup:
        """Клавиатура шага фото: пропустить или отменить."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="⏭ Без фото",
                callback_data="adm_prod_skip_photo",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=AdminCancelCallback().pack(),
            )
        )
        return builder.as_markup()
