import logging
from collections import defaultdict
from functools import lru_cache

from bot.services.commands.base import Command

logger = logging.getLogger(__name__)

# Сколько команд хранить на админа (старые отбрасываются)
MAX_HISTORY_PER_ADMIN = 20


class CommandHistory:
    """Стек выполненных команд per-admin.

    In-memory, теряется при рестарте процесса. Это намеренное упрощение
    учебного проекта: в продакшене история живёт в БД.
    """

    def __init__(self) -> None:
        self._stacks: dict[int, list[Command]] = defaultdict(list)

    def push(self, command: Command) -> None:
        """Добавить выполненную команду в стек админа."""
        if command.executor_user_id is None:
            logger.warning("Command without executor_user_id, not stored")
            return

        admin_id = command.executor_user_id
        stack = self._stacks[admin_id]
        stack.append(command)

        # Лимит размера
        if len(stack) > MAX_HISTORY_PER_ADMIN:
            stack.pop(0)

        logger.info(
            "Command pushed: admin=%d %r (depth=%d)",
            admin_id,
            command.summary,
            len(stack),
        )

    def pop(self, admin_id: int) -> Command | None:
        """Извлечь последнюю команду админа (для undo). None если пусто."""
        stack = self._stacks.get(admin_id)
        if not stack:
            return None
        command = stack.pop()
        logger.info("Command popped for undo: admin=%d %r", admin_id, command.summary)
        return command

    def peek(self, admin_id: int) -> Command | None:
        """Посмотреть последнюю команду без извлечения."""
        stack = self._stacks.get(admin_id)
        if not stack:
            return None
        return stack[-1]

    def list_for_admin(self, admin_id: int) -> list[Command]:
        """Вся история конкретного админа (новейшие в конце)."""
        return list(self._stacks.get(admin_id, []))

    def clear(self) -> None:
        """Очистить всю историю (для тестов)."""
        self._stacks.clear()


@lru_cache(maxsize=1)
def get_command_history() -> CommandHistory:
    """Singleton истории команд на процесс."""
    return CommandHistory()
