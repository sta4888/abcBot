import logging

from aiogram import Bot

from bot.config import get_settings
from bot.db.session import get_session_factory
from bot.repositories.order_repository import OrderRepository
from bot.services.events.base import EventObserver, OrderEvent

logger = logging.getLogger(__name__)

# Какие события интересны админам
ADMIN_INTERESTING_EVENTS = {"order.paid", "order.cancelled"}


class AdminNotifierObserver(EventObserver):
    """Шлёт админам уведомления о событиях.

    Сейчас админы определяются через .env (BOT__ADMIN_IDS).
    В итерации 7 переедет на проверку User.is_admin в БД.
    """

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def handle(self, event: OrderEvent) -> None:
        if event.name not in ADMIN_INTERESTING_EVENTS:
            return

        admin_ids = self._get_admin_ids()
        if not admin_ids:
            return

        # Получаем детали заказа для информативного сообщения
        session_factory = get_session_factory()
        async with session_factory() as session:
            order = await OrderRepository(session).get_by_id(event.order_id)
            if order is None:
                return
            text = self._format_message(event, order)

        for admin_id in admin_ids:
            try:
                await self._bot.send_message(chat_id=admin_id, text=text)
            except Exception:
                logger.exception("Failed to send admin notification to %d", admin_id)

    @staticmethod
    def _get_admin_ids() -> list[int]:
        """Сейчас не настроено в .env, поэтому пустой список (но место есть)."""
        # У нас в .env нет BOT__ADMIN_IDS — оставим пустой, но архитектура готова
        _ = get_settings()
        return []

    @staticmethod
    def _format_message(event: OrderEvent, order: object) -> str:
        if event.name == "order.paid":
            return (
                f"💰 <b>Новый оплаченный заказ #{event.order_id}</b>\n"
                f"Сумма: {order.total / 100:.2f}₽\n"  # type: ignore[attr-defined]
                f"Адрес: <code>{order.delivery_address}</code>\n"  # type: ignore[attr-defined]
                f"Телефон: <code>{order.contact_phone}</code>"  # type: ignore[attr-defined]
            )
        if event.name == "order.cancelled":
            return f"❌ Отменён заказ #{event.order_id}\nСумма: {order.total / 100:.2f}₽"  # type: ignore[attr-defined]
        return f"Событие: {event.name} order={event.order_id}"
