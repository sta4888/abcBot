import asyncio
import logging

from bot.config import settings

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запуск бота."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Bot starting... (пока заглушка)")
    # Реальная инициализация диспетчера появится на следующих шагах
    _ = settings  # чтобы mypy не жаловался на неиспользуемый импорт


if __name__ == "__main__":
    asyncio.run(main())
