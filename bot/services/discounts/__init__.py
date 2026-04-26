from bot.services.discounts.base import PriceCalculator
from bot.services.discounts.base_total import BaseTotal
from bot.services.discounts.decorators import (
    LoyaltyDiscount,
    MinimumTotalGuard,
    PriceDecorator,
    PromoCodeDiscount,
    SeasonalDiscount,
)
from bot.services.discounts.promo_codes import (
    PromoCodeRule,
    lookup_promo_code,
)

__all__ = [
    "BaseTotal",
    "LoyaltyDiscount",
    "MinimumTotalGuard",
    "PriceCalculator",
    "PriceDecorator",
    "PromoCodeDiscount",
    "PromoCodeRule",
    "SeasonalDiscount",
    "calculate_preview_total",
    "lookup_promo_code",
]


def calculate_preview_total(
    items: list,  # type: ignore[type-arg]
    promo_code: str | None,
    seasonal_percent: int,
) -> int:
    """Расчёт суммы для preview (без обращения к БД).

    Применяет промокод и сезонную скидку. Лояльность нет (требует БД).
    """
    calc: PriceCalculator = BaseTotal(items)

    if promo_code:
        rule = lookup_promo_code(promo_code)
        if rule is not None:
            calc = PromoCodeDiscount(calc, percent=rule.percent, flat_kopecks=rule.flat_kopecks)

    if seasonal_percent > 0:
        calc = SeasonalDiscount(calc, percent=seasonal_percent)

    calc = MinimumTotalGuard(calc, minimum=0)
    return calc.calculate()
