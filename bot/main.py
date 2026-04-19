import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings
from bot.handlers import main_router
from bot.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запуск бота в режиме long-polling."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    bot = Bot(
        token=settings.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(main_router)

    logger.info("Bot starting in polling mode...")

    # Удаляем накопленные апдейты, чтобы не ловить старое при рестарте
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
