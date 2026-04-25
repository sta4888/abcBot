import logging

from bot.services.events.base import EventObserver, OrderEvent

logger = logging.getLogger(__name__)


class LoggingObserver(EventObserver):
    """Пишет каждое событие в лог. Никаких побочных эффектов кроме лога."""

    async def handle(self, event: OrderEvent) -> None:
        logger.info("Event: %s order_id=%d", event.name, event.order_id)
