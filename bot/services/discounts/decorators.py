import logging

from bot.services.discounts.base import PriceCalculator

logger = logging.getLogger(__name__)


class PriceDecorator(PriceCalculator):
    """Промежуточный базовый класс для декораторов.

    Хранит ссылку на оборачиваемый объект (wrappee).
    Конкретные декораторы переопределяют calculate(), вызывая super().calculate()
    или wrappee.calculate() и применяя модификацию.
    """

    def __init__(self, wrappee: PriceCalculator) -> None:
        self._wrappee = wrappee

    def calculate(self) -> int:
        return self._wrappee.calculate()


# ─── Скидки ──────────────────────────────────────────────────────


class PromoCodeDiscount(PriceDecorator):
    """Скидка по промокоду.

    Принимает уже разрешённую скидку (процент ИЛИ фикс. сумма):
    - percent: 10 = -10%
    - flat_kopecks: 30000 = -300₽

    Только один из них должен быть задан.
    """

    def __init__(
        self,
        wrappee: PriceCalculator,
        percent: int | None = None,
        flat_kopecks: int | None = None,
    ) -> None:
        super().__init__(wrappee)
        if (percent is None) == (flat_kopecks is None):
            raise ValueError("PromoCodeDiscount requires exactly one of percent / flat_kopecks")
        self._percent = percent
        self._flat = flat_kopecks

    def calculate(self) -> int:
        base = self._wrappee.calculate()
        if self._percent is not None:
            discount = base * self._percent // 100
        else:
            assert self._flat is not None
            discount = self._flat
        result = base - discount
        logger.debug(
            "PromoCodeDiscount: base=%d discount=%d -> %d",
            base,
            discount,
            result,
        )
        return result


class SeasonalDiscount(PriceDecorator):
    """Сезонная скидка: фиксированный процент."""

    def __init__(self, wrappee: PriceCalculator, percent: int) -> None:
        super().__init__(wrappee)
        if not 0 < percent < 100:
            raise ValueError("Seasonal percent must be in (0; 100)")
        self._percent = percent

    def calculate(self) -> int:
        base = self._wrappee.calculate()
        discount = base * self._percent // 100
        result = base - discount
        logger.debug(
            "SeasonalDiscount(%d%%): base=%d discount=%d -> %d",
            self._percent,
            base,
            discount,
            result,
        )
        return result


class LoyaltyDiscount(PriceDecorator):
    """Скидка лояльности — фиксированный процент."""

    def __init__(self, wrappee: PriceCalculator, percent: int = 5) -> None:
        super().__init__(wrappee)
        if not 0 < percent < 100:
            raise ValueError("Loyalty percent must be in (0; 100)")
        self._percent = percent

    def calculate(self) -> int:
        base = self._wrappee.calculate()
        discount = base * self._percent // 100
        result = base - discount
        logger.debug(
            "LoyaltyDiscount(%d%%): base=%d discount=%d -> %d",
            self._percent,
            base,
            discount,
            result,
        )
        return result


# ─── Защитный слой ───────────────────────────────────────────────


class MinimumTotalGuard(PriceDecorator):
    """Защита: итог не уходит ниже минимума (по умолчанию 0).

    Это тоже декоратор, но не скидка — он защищает от 'отрицательной суммы',
    если все скидки в сумме больше базы.
    """

    def __init__(self, wrappee: PriceCalculator, minimum: int = 0) -> None:
        super().__init__(wrappee)
        if minimum < 0:
            raise ValueError("Minimum cannot be negative")
        self._minimum = minimum

    def calculate(self) -> int:
        result = max(self._minimum, self._wrappee.calculate())
        return result
