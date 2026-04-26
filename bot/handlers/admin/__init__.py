from aiogram import Router

from bot.handlers.admin.categories import router as admin_categories_router
from bot.handlers.admin.menu import router as admin_menu_router
from bot.handlers.admin.orders import router as admin_orders_router
from bot.handlers.admin.products import router as admin_products_router

admin_main_router = Router(name="admin.main")
# Специфичные раньше
admin_main_router.include_router(admin_categories_router)
admin_main_router.include_router(admin_products_router)
admin_main_router.include_router(admin_orders_router)
# Меню в конце (там F.text фильтры на кнопки)
admin_main_router.include_router(admin_menu_router)
