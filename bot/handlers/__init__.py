from aiogram import Router

from bot.handlers.user.start import router as user_start_router

main_router = Router(name="main")
main_router.include_router(user_start_router)
