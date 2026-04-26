from aiogram import Router

from bot.handlers.admin import admin_main_router
from bot.handlers.user.cart import router as user_cart_router
from bot.handlers.user.catalog import router as user_catalog_router
from bot.handlers.user.checkout import router as user_checkout_router
from bot.handlers.user.menu import router as user_menu_router
from bot.handlers.user.orders import router as user_orders_router
from bot.handlers.user.start import router as user_start_router

main_router = Router(name="main")

# Админские роутеры — раньше пользовательских (чтобы /admin_ship не словился общим catch-all)
main_router.include_router(admin_main_router)

# Пользовательские специфичные
main_router.include_router(user_catalog_router)
main_router.include_router(user_cart_router)
main_router.include_router(user_checkout_router)
main_router.include_router(user_orders_router)
main_router.include_router(user_menu_router)

# Общие фолбэки
main_router.include_router(user_start_router)
