# abcBot
bot





------------------------------------------------

uv add <pkg>              # добавить зависимость

uv add --dev <pkg>        # добавить dev-зависимость

uv remove <pkg>            # удалить зависимость

uv sync                   # синхронизировать .venv с lock-файлом

uv lock                   # пересчитать lock-файл

uv run <command>          # запустить команду в .venv

uv run python <file>      # запустить скрипт

uv tree                   # дерево зависимостей

uv python list            # список установленных Python

uv python install 3.12    # установить Python 3.12

-------------------------

Типы, которые будем использовать:

feat — новая функциональность (добавил корзину)

fix — починил баг

chore — рутина (обновил зависимости, настроил инструменты)

docs — правки документации

refactor — рефакторинг без изменения поведения

test — добавил/изменил тесты

style — форматирование, пробелы, опечатки в коде

perf — ускорение без изменения функционала

ci — правки CI/CD

#### примеры...

feat(catalog): add product listing by category

fix(cart): prevent adding out-of-stock items

chore(deps): add aiogram and pydantic-settings

refactor(payment): extract PaymentStrategy interface

docs(readme): describe project structure

---------------------------

упрощённый GitHub Flow:

main — всегда рабочее, стабильное состояние. В неё попадают только протестированные вещи.

dev — интеграционная ветка, сюда сливаются фичи перед тем как пойти в main. На старте можно даже без неё обойтись, но я рекомендую завести — привыкнешь к флоу.

feature/<название> — на каждую крупную фичу. Например feature/catalog, feature/payment-strategy.

fix/<название> — на баги.

----------------------------

Для старта нам нужны:

BOT_TOKEN — токен от BotFather

ADMIN_IDS — Telegram ID админов через запятую

POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB — креды БД

REDIS_HOST, REDIS_PORT, REDIS_DB — креды Redis

DEBUG — флаг разработки (подробные логи и т. д.)
