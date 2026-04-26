import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import get_settings
from bot.handlers import main_router
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.middlewares.db_middleware import DatabaseMiddleware
from bot.services.events import get_event_bus
from bot.services.events.observers import (
    AdminNotifierObserver,
    LoggingObserver,
    UserNotifierObserver,
)
from bot.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запуск бота в режиме long-polling."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

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

    # Outer middleware — выполняются ДО фильтров. Это критично:
    # AdminFilter читает current_user из data, и эта переменная должна
    # быть положена туда AuthMiddleware заранее.
    dispatcher.message.outer_middleware(DatabaseMiddleware())
    dispatcher.callback_query.outer_middleware(DatabaseMiddleware())
    dispatcher.message.outer_middleware(AuthMiddleware())
    dispatcher.callback_query.outer_middleware(AuthMiddleware())

    dispatcher.include_router(main_router)

    # Регистрация EventBus подписчиков
    event_bus = get_event_bus()
    event_bus.subscribe(LoggingObserver())
    event_bus.subscribe(UserNotifierObserver(bot=bot))
    event_bus.subscribe(AdminNotifierObserver(bot=bot))
    logger.info("Event observers registered")

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
