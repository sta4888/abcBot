from aiogram import Router

from bot.handlers.admin.menu import router as admin_menu_router
from bot.handlers.admin.orders import router as admin_orders_router

# Главный роутер админки — для удобства подключения в main_router
admin_main_router = Router(name="admin.main")
admin_main_router.include_router(admin_menu_router)
admin_main_router.include_router(admin_orders_router)
