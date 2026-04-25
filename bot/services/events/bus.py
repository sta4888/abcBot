import logging
from contextlib import suppress
from functools import lru_cache

from bot.services.events.base import EventObserver, OrderEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Шина событий: подписки + публикация.

    Подписчики обрабатываются последовательно. Если один упал —
    логируем и продолжаем (не должны блокировать других).
    """

    def __init__(self) -> None:
        self._observers: list[EventObserver] = []

    def subscribe(self, observer: EventObserver) -> None:
        """Подписывает наблюдателя на все события."""
        self._observers.append(observer)
        logger.debug("Subscribed observer: %s", type(observer).__name__)

    def unsubscribe(self, observer: EventObserver) -> None:
        """Удаляет наблюдателя из подписки."""
        with suppress(ValueError):
            self._observers.remove(observer)

    async def publish(self, event: OrderEvent) -> None:
        """Публикует событие — оповещает всех подписчиков.

        Каждый подписчик в своём try/except: ошибка не валит остальных.
        """
        for observer in self._observers:
            try:
                await observer.handle(event)
            except Exception:
                logger.exception(
                    "Observer %s failed on event %s",
                    type(observer).__name__,
                    event.name,
                )

    def clear(self) -> None:
        """Удаляет всех подписчиков. Полезно в тестах."""
        self._observers.clear()


@lru_cache(maxsize=1)
def get_event_bus() -> EventBus:
    """Singleton EventBus на процесс."""
    return EventBus()
