from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Кнопки админа
ADMIN_BTN_PRODUCTS = "🛍 Товары"
ADMIN_BTN_CATEGORIES = "📂 Категории"
ADMIN_BTN_ORDERS = "📦 Заказы"
ADMIN_BTN_EXIT = "🚪 Выйти из админки"


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Главное меню админа."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_BTN_CATEGORIES), KeyboardButton(text=ADMIN_BTN_PRODUCTS)],
            [KeyboardButton(text=ADMIN_BTN_ORDERS)],
            [KeyboardButton(text=ADMIN_BTN_EXIT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
