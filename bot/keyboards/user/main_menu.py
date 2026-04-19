from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Тексты кнопок — константы, чтобы в хендлерах сравнивать без магических строк
BTN_CATALOG = "🛍 Каталог"
BTN_CART = "🛒 Корзина"
BTN_ORDERS = "📦 Мои заказы"
BTN_HELP = "ℹ️ Помощь"


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню пользователя — отображается внизу экрана."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_CART)],
            [KeyboardButton(text=BTN_ORDERS), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,  # чтобы клавиатура была компактной, не вида «телефон»
        is_persistent=True,  # чтобы не скрывалась при отправке сообщения
    )
