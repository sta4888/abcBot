from aiogram import Router

from bot.handlers.user.menu import router as user_menu_router
from bot.handlers.user.start import router as user_start_router

main_router = Router(name="main")

# Сначала специфичные роутеры (кнопки, callback'и)
main_router.include_router(user_menu_router)

# Потом — роутеры с широкими фолбэками (/start и catch-all)
main_router.include_router(user_start_router)
