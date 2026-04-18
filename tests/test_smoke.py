"""Smoke-тесты — проверяют, что окружение в принципе живое."""


def test_python_works() -> None:
    """Базовый sanity check: Python вообще выполняет код."""
    assert 1 + 1 == 2


def test_imports_work() -> None:
    """Проверяем, что ключевые зависимости импортируются."""
    import aiogram  # noqa: F401
    import pydantic_settings  # noqa: F401
