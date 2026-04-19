import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import get_settings
from bot.handlers import main_router
from bot.middlewares.db_middleware import DatabaseMiddleware
from bot.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запуск бота в режиме long-polling."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    # Redis для FSM
    redis = Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
    )
    storage = RedisStorage(redis=redis)

    bot = Bot(
        token=settings.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=storage)

    # Middleware: один на message, один на callback_query
    dispatcher.message.middleware(DatabaseMiddleware())
    dispatcher.callback_query.middleware(DatabaseMiddleware())

    dispatcher.include_router(main_router)

    logger.info("Bot starting in polling mode...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.aclose()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
