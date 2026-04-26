import logging
from datetime import UTC, datetime

from bot.services.commands.base import Command, CommandError
from bot.services.order_service import OrderService

logger = logging.getLogger(__name__)


class _BaseOrderCommand(Command):
    """Общий базовый класс — переиспользуем поля и summary."""

    def __init__(self, order_id: int, executor_user_id: int) -> None:
        super().__init__()
        self._order_id = order_id
        self.executor_user_id = executor_user_id

    def _service(self) -> OrderService:
        """OrderService на текущей привязанной сессии."""
        return OrderService(self._require_session())


class ShipOrderCommand(_BaseOrderCommand):
    """Отправить заказ. paid → shipped. Откат: shipped → paid."""

    def __init__(self, order_id: int, executor_user_id: int) -> None:
        super().__init__(order_id, executor_user_id)
        self.summary = f"Отправить заказ #{order_id}"

    async def execute(self) -> bool:
        order = await self._service().ship_order(self._order_id)
        if order is None:
            return False
        self.executed_at = datetime.now(UTC)
        return True

    async def undo(self) -> bool:
        service = self._service()
        order = await service._order_repo.get_by_id(self._order_id)
        if order is None:
            return False
        result = await service._apply_transition(order, action="revert_ship")
        return result is not None


class DeliverOrderCommand(_BaseOrderCommand):
    """Пометить доставленным. shipped → delivered. Откат: → shipped."""

    def __init__(self, order_id: int, executor_user_id: int) -> None:
        super().__init__(order_id, executor_user_id)
        self.summary = f"Доставить заказ #{order_id}"

    async def execute(self) -> bool:
        order = await self._service().deliver_order(self._order_id)
        if order is None:
            return False
        self.executed_at = datetime.now(UTC)
        return True

    async def undo(self) -> bool:
        service = self._service()
        order = await service._order_repo.get_by_id(self._order_id)
        if order is None:
            return False
        result = await service._apply_transition(order, action="revert_deliver")
        return result is not None


class AdminCancelOrderCommand(_BaseOrderCommand):
    """Админская отмена. * → cancelled. Откат: → previous_status."""

    def __init__(self, order_id: int, executor_user_id: int) -> None:
        super().__init__(order_id, executor_user_id)
        self.summary = f"Отменить заказ #{order_id}"
        self._previous_status: str | None = None

    async def execute(self) -> bool:
        service = self._service()
        order = await service._order_repo.get_by_id(self._order_id)
        if order is None:
            return False
        self._previous_status = order.status

        result = await service._apply_transition(order, action="cancel")
        if result is None:
            return False
        self.executed_at = datetime.now(UTC)
        return True

    async def undo(self) -> bool:
        if self._previous_status is None:
            raise CommandError("Cannot undo cancel: previous_status not stored")
        service = self._service()
        order = await service._order_repo.get_by_id(self._order_id)
        if order is None:
            return False
        result = await service._apply_transition(
            order,
            action="revert_cancel",
            previous_status=self._previous_status,
        )
        return result is not None
