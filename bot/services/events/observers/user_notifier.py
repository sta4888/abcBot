import logging

from aiogram import Bot

from bot.db.session import get_session_factory
from bot.repositories.order_repository import OrderRepository
from bot.services.events.base import EventObserver, OrderEvent

logger = logging.getLogger(__name__)

# Тексты для каждого вида события
EVENT_USER_MESSAGES = {
    "order.paid": "✅ Заказ <b>#{order_id}</b> оплачен. Скоро мы займёмся им!",
    "order.shipped": "🚚 Заказ <b>#{order_id}</b> отправлен.",
    "order.delivered": "📦 Заказ <b>#{order_id}</b> доставлен. Спасибо за покупку!",
    "order.cancelled": "❌ Заказ <b>#{order_id}</b> отменён.",
}


class UserNotifierObserver(EventObserver):
    """Уведомляет пользователя в Telegram по событиям его заказов."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def handle(self, event: OrderEvent) -> None:
        """Получаем заказ → шлём пользователю сообщение."""
        template = EVENT_USER_MESSAGES.get(event.name)
        if template is None:
            return  # неизвестное событие — игнорируем

        # Используем независимую сессию: транзакция middleware уже могла закрыться
        session_factory = get_session_factory()
        async with session_factory() as session:
            order = await OrderRepository(session).get_by_id(event.order_id)
            if order is None:
                logger.warning("UserNotifier: order %d not found", event.order_id)
                return
            user_telegram_id = order.user_id

        text = template.format(order_id=event.order_id)

        try:
            await self._bot.send_message(chat_id=user_telegram_id, text=text)
        except Exception:
            # Юзер мог заблокировать бота — это нормально, логируем и идём дальше
            logger.exception(
                "Failed to send user notification: order=%d user=%d",
                event.order_id,
                user_telegram_id,
            )
