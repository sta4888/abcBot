import asyncio
import logging

from bot.config import get_settings
from bot.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запуск бота."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    logger.info("Bot starting... (пока заглушка, диспетчер появится позже)")
    logger.debug("Debug mode enabled, settings loaded")


if __name__ == "__main__":
    asyncio.run(main())
