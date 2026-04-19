import logging
import sys

from colorlog import ColoredFormatter


def setup_logging(debug: bool = False) -> None:
    """Настраивает корневой логгер и подавляет шумные сторонние логгеры.

    Args:
        debug: если True — уровень DEBUG, иначе INFO.
    """
    level = logging.DEBUG if debug else logging.INFO

    # Цветной форматтер для dev-вывода
    formatter = ColoredFormatter(
        fmt=(
            "%(log_color)s%(asctime)s%(reset)s "
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(cyan)s%(name)s%(reset)s: "
            "%(message)s"
        ),
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "white",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Настраиваем корневой логгер
    root = logging.getLogger()
    root.setLevel(level)
    # Убираем хендлеры по умолчанию (basicConfig), чтобы не было дублирования
    root.handlers.clear()
    root.addHandler(handler)

    # Подавляем шумные чужие логгеры
    # aiogram.event — каждый апдейт пишет "Update id=... is handled"
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    # SQLAlchemy echo мы уже отключили через SQL_ECHO, но на всякий случай
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
