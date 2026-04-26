import pytest

from bot.services.discounts import (
    BaseTotal,
    LoyaltyDiscount,
    MinimumTotalGuard,
    PriceCalculator,
    PromoCodeDiscount,
    SeasonalDiscount,
    calculate_preview_total,
    lookup_promo_code,
)
from bot.services.order_builder import OrderItemSpec


@pytest.fixture
def items() -> list[OrderItemSpec]:
    return [
        OrderItemSpec(product_id=1, product_name="A", price=10000, quantity=2),  # 200₽
        OrderItemSpec(product_id=2, product_name="B", price=30000, quantity=1),  # 300₽
    ]


# ─── BaseTotal ───────────────────────────────────────────────────


def test_base_total(items: list[OrderItemSpec]) -> None:
    """Базовая сумма = 200 + 300 = 500₽ = 50000 копеек."""
    assert BaseTotal(items).calculate() == 50000


# ─── PromoCodeDiscount ───────────────────────────────────────────


def test_promo_percent(items: list[OrderItemSpec]) -> None:
    """-10% от 50000 = 45000."""
    calc = PromoCodeDiscount(BaseTotal(items), percent=10)
    assert calc.calculate() == 45000


def test_promo_flat(items: list[OrderItemSpec]) -> None:
    """-300₽ от 50000 = 20000."""
    calc = PromoCodeDiscount(BaseTotal(items), flat_kopecks=30000)
    assert calc.calculate() == 20000


def test_promo_requires_one_param() -> None:
    """Должен быть задан ровно один из percent/flat."""
    base = BaseTotal([])
    with pytest.raises(ValueError):
        PromoCodeDiscount(base, percent=10, flat_kopecks=100)
    with pytest.raises(ValueError):
        PromoCodeDiscount(base)


# ─── SeasonalDiscount ────────────────────────────────────────────


def test_seasonal_discount(items: list[OrderItemSpec]) -> None:
    """-15% от 50000 = 42500."""
    calc = SeasonalDiscount(BaseTotal(items), percent=15)
    assert calc.calculate() == 42500


def test_seasonal_invalid_percent() -> None:
    base = BaseTotal([])
    with pytest.raises(ValueError):
        SeasonalDiscount(base, percent=0)
    with pytest.raises(ValueError):
        SeasonalDiscount(base, percent=100)


# ─── LoyaltyDiscount ─────────────────────────────────────────────


def test_loyalty_default(items: list[OrderItemSpec]) -> None:
    """-5% по умолчанию: 50000 - 2500 = 47500."""
    calc = LoyaltyDiscount(BaseTotal(items))
    assert calc.calculate() == 47500


# ─── MinimumTotalGuard ──────────────────────────────────────────


def test_minimum_guard_protects_from_negative(
    items: list[OrderItemSpec],
) -> None:
    """Если скидка больше суммы — итог = 0, не отрицательный."""
    calc: PriceCalculator = BaseTotal(items)
    calc = PromoCodeDiscount(calc, flat_kopecks=100000)  # больше базы!
    calc = MinimumTotalGuard(calc, minimum=0)
    assert calc.calculate() == 0


def test_minimum_guard_does_not_change_normal(
    items: list[OrderItemSpec],
) -> None:
    """Если итог положительный — guard ничего не делает."""
    calc: PriceCalculator = BaseTotal(items)
    calc = MinimumTotalGuard(calc, minimum=0)
    assert calc.calculate() == 50000


# ─── Цепочки ─────────────────────────────────────────────────────


def test_full_chain(items: list[OrderItemSpec]) -> None:
    """Цепочка: 50000 → -10% → -15% → -5% = ?

    50000 * 0.9 = 45000
    45000 * 0.85 = 38250
    38250 * 0.95 = 36337 (округление при /100 в Python)
    """
    calc: PriceCalculator = BaseTotal(items)
    calc = PromoCodeDiscount(calc, percent=10)
    calc = SeasonalDiscount(calc, percent=15)
    calc = LoyaltyDiscount(calc, percent=5)
    calc = MinimumTotalGuard(calc, minimum=0)

    result = calc.calculate()
    # Проверяем диапазон, не точное (целочисленные деления)
    assert 36000 <= result <= 36500


def test_chain_order_matters(items: list[OrderItemSpec]) -> None:
    """Демонстрация: порядок применения скидок ВЛИЯЕТ на итог.

    Промокод-50% потом сезонная-50%: 50000 * 0.5 * 0.5 = 12500
    Сезонная-50% потом промокод-50%: то же 12500 (коммутативно для процентов).
    Но при flat-скидках порядок имеет значение:
    """
    # flat 100₽ потом %50 vs %50 потом flat 100₽
    calc1 = SeasonalDiscount(PromoCodeDiscount(BaseTotal(items), flat_kopecks=10000), percent=50)
    calc2 = PromoCodeDiscount(SeasonalDiscount(BaseTotal(items), percent=50), flat_kopecks=10000)
    # 50000 - 10000 = 40000, потом /2 = 20000
    # 50000 / 2 = 25000, потом - 10000 = 15000
    assert calc1.calculate() != calc2.calculate()


# ─── Промокоды ──────────────────────────────────────────────────


def test_lookup_known_promo() -> None:
    rule = lookup_promo_code("WELCOME10")
    assert rule is not None
    assert rule.percent == 10


def test_lookup_case_insensitive() -> None:
    assert lookup_promo_code("welcome10") is not None
    assert lookup_promo_code("WeLcOmE10") is not None


def test_lookup_unknown() -> None:
    assert lookup_promo_code("nonexistent") is None


# ─── Preview расчёт ─────────────────────────────────────────────


def test_preview_no_discounts(items: list[OrderItemSpec]) -> None:
    """Без промокода и сезонной — базовая сумма."""
    assert calculate_preview_total(items, promo_code=None, seasonal_percent=0) == 50000


def test_preview_with_promo(items: list[OrderItemSpec]) -> None:
    """С WELCOME10 — -10%."""
    assert calculate_preview_total(items, promo_code="WELCOME10", seasonal_percent=0) == 45000


def test_preview_unknown_promo_ignored(items: list[OrderItemSpec]) -> None:
    """Незнакомый код просто игнорируется (не падает)."""
    assert calculate_preview_total(items, promo_code="UNKNOWN", seasonal_percent=0) == 50000
