from abc import ABC, abstractmethod


class PriceCalculator(ABC):
    """Абстрактный калькулятор суммы. Декораторы реализуют этот же интерфейс."""

    @abstractmethod
    def calculate(self) -> int:
        """Возвращает итог в копейках."""
