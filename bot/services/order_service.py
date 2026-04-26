import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.models import Order
from bot.repositories.cart_repository import CartRepository
from bot.repositories.order_repository import OrderRepository
from bot.services.discounts import (
    BaseTotal,
    LoyaltyDiscount,
    MinimumTotalGuard,
    PriceCalculator,
    PromoCodeDiscount,
    SeasonalDiscount,
    lookup_promo_code,
)
from bot.services.order_builder import OrderBuilder
from bot.services.payment import PaymentInitResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OrderSummaryView:
    """Краткое представление заказа для списка 'Мои заказы'."""

    order: Order
    items_count: int


# Человекочитаемые названия статусов для UI
STATUS_LABELS = {
    "new": "🆕 Новый",
    "paid": "💰 Оплачен",
    "shipped": "🚚 Отправлен",
    "delivered": "✅ Доставлен",
    "cancelled": "❌ Отменён",
}


class OrderService:
    """Фасад над работой с заказами."""

    def __init__(self, session: AsyncSession) -> None:
        self._order_repo = OrderRepository(session)
        self._cart_repo = CartRepository(session)

    async def list_user_orders(self, user_id: int) -> list[OrderSummaryView]:
        """Возвращает заказы пользователя для экрана 'Мои заказы'."""
        orders = await self._order_repo.list_by_user(user_id)
        return [
            OrderSummaryView(
                order=order,
                items_count=sum(item.quantity for item in order.items),
            )
            for order in orders
        ]

    async def create_order_from_builder(self, builder: OrderBuilder) -> Order:
        """Создаёт заказ по данным билдера и очищает корзину пользователя.

        Применяет цепочку скидок (Decorator) к итогу:
            BaseTotal → PromoCode → Seasonal → Loyalty → MinimumGuard
        """
        # 1. Строим Order через Builder (он считает item-ы как раньше)
        order = builder.build()

        # 2. Пересчитываем total через цепочку Decorator
        order.total = await self._calculate_total_with_discounts(builder)

        # 3. Сохраняем
        self._order_repo.add(order)
        await self._order_repo._session.flush()

        await self._cart_repo.clear_user_cart(builder.user_id)

        logger.info(
            "Order created: id=%d user_id=%d total=%.2f₽",
            order.id,
            order.user_id,
            order.total / 100,
        )
        return order

    async def _calculate_total_with_discounts(self, builder: OrderBuilder) -> int:
        """Собирает цепочку Decorator и считает итог.

        Состав цепочки зависит от контекста:
        - Промокод указан → PromoCodeDiscount
        - Сезонная скидка > 0 в конфиге → SeasonalDiscount
        - У юзера >= 3 оплаченных заказов → LoyaltyDiscount
        Финальный слой: MinimumTotalGuard (защита от ухода в минус).
        """
        # 1. Корень: базовая сумма по позициям
        calc: PriceCalculator = BaseTotal(builder.items)

        # 2. Промокод
        if builder.promo_code:
            rule = lookup_promo_code(builder.promo_code)
            if rule is not None:
                calc = PromoCodeDiscount(
                    calc,
                    percent=rule.percent,
                    flat_kopecks=rule.flat_kopecks,
                )

        # 3. Сезонная скидка
        seasonal = get_settings().seasonal_discount_percent
        if seasonal > 0:
            calc = SeasonalDiscount(calc, percent=seasonal)

        # 4. Лояльность: считаем оплаченные заказы юзера
        paid_count = await self._order_repo.count_paid_by_user(builder.user_id)
        if paid_count >= 3:
            calc = LoyaltyDiscount(calc, percent=5)

        # 5. Защитный нижний порог
        calc = MinimumTotalGuard(calc, minimum=0)

        return calc.calculate()

    async def initiate_payment(self, order: Order) -> "PaymentInitResult":
        """Инициирует оплату через стратегию."""
        from bot.services.payment import get_payment_factory

        strategy = get_payment_factory().get(order.payment_method)
        return await strategy.create_payment(order)

    async def confirm_payment(self, order_id: int, user_id: int) -> Order | None:
        """Подтверждает оплату через стратегию + State-переход new → paid.

        Возвращает Order при успехе, None — если:
        - заказ не найден или принадлежит другому пользователю
        - переход недоступен в текущем статусе
        - стратегия не подтвердила оплату
        """
        from bot.services.payment import get_payment_factory

        order = await self._order_repo.get_by_id(order_id)
        if order is None or order.user_id != user_id:
            return None

        # Stage 1: Стратегия проверяет оплату
        strategy = get_payment_factory().get(order.payment_method)
        if not await strategy.verify_payment(order):
            logger.info("Payment not verified for order %d", order_id)
            return None

        # Stage 2: State-машина выполняет переход
        return await self._apply_transition(order, action="pay")

    async def cancel_order(self, order_id: int, user_id: int) -> Order | None:
        """Отменяет заказ. None — если заказ не найден / переход запрещён."""
        order = await self._order_repo.get_by_id(order_id)
        if order is None or order.user_id != user_id:
            return None
        return await self._apply_transition(order, action="cancel")

    async def ship_order(self, order_id: int) -> Order | None:
        """Админский переход paid → shipped. None при ошибке.

        TODO в ит. 7: добавить проверку, что вызывающий — админ.
        """
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            return None
        return await self._apply_transition(order, action="ship")

    async def deliver_order(self, order_id: int) -> Order | None:
        """Админский переход shipped → delivered."""
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            return None
        return await self._apply_transition(order, action="deliver")

    async def _apply_transition(
        self,
        order: Order,
        action: str,
        **action_kwargs: object,
    ) -> Order | None:
        """Применяет State-переход к заказу + публикует событие.

        action — имя метода в OrderState ('pay', 'ship', 'revert_ship', ...).
        action_kwargs — дополнительные аргументы метода (например, previous_status).
        """
        from bot.domain.order_states import (
            InvalidTransitionError,
            get_order_state,
        )
        from bot.services.events import OrderEvent, get_event_bus

        state = get_order_state(order.status)
        method = getattr(state, action, None)
        if method is None:
            logger.warning("Unknown action: %s", action)
            return None

        try:
            transition = method(**action_kwargs)
        except InvalidTransitionError as e:
            logger.info("Order %d: %s transition refused (%s)", order.id, action, e)
            return None

        old_status = order.status
        order.status = transition.new_status
        await self._order_repo._session.flush()

        logger.info(
            "Order %d: %s -> %s (event=%s)",
            order.id,
            old_status,
            transition.new_status,
            transition.event_name,
        )

        await get_event_bus().publish(OrderEvent(name=transition.event_name, order_id=order.id))

        return order
