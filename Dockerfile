# syntax=docker/dockerfile:1.7

# ======== Этап 1: билд зависимостей ========
FROM python:3.12-slim AS builder

# Ставим uv копированием из официального образа — быстрее и без пакетного менеджера
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Копируем ТОЛЬКО файлы управления зависимостями — используем кэш Docker слоёв
COPY pyproject.toml uv.lock ./

# Ставим зависимости в отдельный venv, без dev-группы
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

RUN uv sync --frozen --no-install-project --no-dev


# ======== Этап 2: финальный образ ========
FROM python:3.12-slim AS runtime

# Непривилегированный пользователь — так надёжнее
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app

# Копируем venv из builder-этапа
COPY --from=builder /app/.venv /app/.venv

# Копируем код приложения
COPY bot/ ./bot/
COPY pyproject.toml ./

# Добавляем venv в PATH, чтобы python и прочее брались оттуда
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app

CMD ["python", "-m", "bot.main"]
