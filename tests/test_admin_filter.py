from datetime import UTC, datetime

from aiogram.types import Chat, Message
from aiogram.types import User as TgUser

from bot.filters.admin import AdminFilter
from bot.models import User


def _make_message() -> Message:
    """Создаём минимальный Message для теста (без реального обмена с TG)."""
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=1, type="private"),
        from_user=TgUser(id=1, is_bot=False, first_name="Test"),
    )


def _make_user(is_admin: bool) -> User:
    user = User()
    user.id = 1
    user.is_admin = is_admin
    return user


async def test_admin_filter_passes_admin() -> None:
    f = AdminFilter()
    msg = _make_message()
    assert await f(msg, current_user=_make_user(is_admin=True)) is True


async def test_admin_filter_rejects_non_admin() -> None:
    f = AdminFilter()
    msg = _make_message()
    assert await f(msg, current_user=_make_user(is_admin=False)) is False


async def test_admin_filter_rejects_no_user() -> None:
    f = AdminFilter()
    msg = _make_message()
    assert await f(msg, current_user=None) is False
