from bot.services.commands import CommandHistory
from bot.services.commands.base import Command


class FakeCommand(Command):
    """Тестовый Command без внешних зависимостей."""

    def __init__(self, executor_user_id: int, label: str = "fake") -> None:
        super().__init__()
        self.executor_user_id = executor_user_id
        self.summary = label
        self.execute_called = False
        self.undo_called = False
        self.execute_returns = True
        self.undo_returns = True

    async def execute(self) -> bool:
        self.execute_called = True
        return self.execute_returns

    async def undo(self) -> bool:
        self.undo_called = True
        return self.undo_returns


# ─── CommandHistory ───────────────────────────────────────────────


def test_history_push_and_peek() -> None:
    history = CommandHistory()
    cmd = FakeCommand(executor_user_id=1)
    history.push(cmd)

    assert history.peek(1) is cmd


def test_history_pop_removes() -> None:
    history = CommandHistory()
    cmd = FakeCommand(executor_user_id=1)
    history.push(cmd)

    popped = history.pop(1)
    assert popped is cmd
    assert history.peek(1) is None  # стек пуст после pop


def test_history_separate_stacks_per_admin() -> None:
    history = CommandHistory()
    cmd1 = FakeCommand(executor_user_id=1, label="admin1")
    cmd2 = FakeCommand(executor_user_id=2, label="admin2")
    history.push(cmd1)
    history.push(cmd2)

    assert history.peek(1) is cmd1
    assert history.peek(2) is cmd2


def test_history_max_size_truncates() -> None:
    """Сверх лимита — старые отбрасываются."""
    from bot.services.commands.history import MAX_HISTORY_PER_ADMIN

    history = CommandHistory()
    for i in range(MAX_HISTORY_PER_ADMIN + 5):
        history.push(FakeCommand(executor_user_id=1, label=f"cmd{i}"))

    stack = history.list_for_admin(1)
    assert len(stack) == MAX_HISTORY_PER_ADMIN
    # старые отброшены, последняя — последняя из добавленных
    assert stack[-1].summary == f"cmd{MAX_HISTORY_PER_ADMIN + 4}"


def test_history_pop_empty_returns_none() -> None:
    history = CommandHistory()
    assert history.pop(99) is None


def test_history_skips_command_without_executor() -> None:
    """Если у команды нет executor_user_id — она не сохраняется."""
    history = CommandHistory()
    cmd = FakeCommand(executor_user_id=1)
    cmd.executor_user_id = None  # симулируем отсутствие
    history.push(cmd)

    assert history.peek(1) is None


# ─── FakeCommand execute/undo ────────────────────────────────────


async def test_command_execute() -> None:
    cmd = FakeCommand(executor_user_id=1)
    result = await cmd.execute()
    assert result is True
    assert cmd.execute_called is True


async def test_command_undo() -> None:
    cmd = FakeCommand(executor_user_id=1)
    result = await cmd.undo()
    assert result is True
    assert cmd.undo_called is True


async def test_command_failed_execute() -> None:
    cmd = FakeCommand(executor_user_id=1)
    cmd.execute_returns = False
    assert await cmd.execute() is False


# ─── LIFO порядок ────────────────────────────────────────────────


def test_history_is_lifo() -> None:
    """Pop возвращает САМУЮ последнюю выполненную команду."""
    history = CommandHistory()
    history.push(FakeCommand(executor_user_id=1, label="first"))
    history.push(FakeCommand(executor_user_id=1, label="second"))
    history.push(FakeCommand(executor_user_id=1, label="third"))

    assert history.pop(1).summary == "third"  # type: ignore[union-attr]
    assert history.pop(1).summary == "second"  # type: ignore[union-attr]
    assert history.pop(1).summary == "first"  # type: ignore[union-attr]
