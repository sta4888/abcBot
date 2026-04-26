from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromoCodeRule:
    """Правило применения промокода.

    Ровно одно из percent / flat_kopecks должно быть задано.
    """

    percent: int | None = None
    flat_kopecks: int | None = None


_PROMO_CODES: dict[str, PromoCodeRule] = {
    "WELCOME10": PromoCodeRule(percent=10),
    "MINUS300": PromoCodeRule(flat_kopecks=30000),  # 300₽
}


def lookup_promo_code(code: str) -> PromoCodeRule | None:
    """Возвращает правило по коду или None, если не найден.

    Сравнение регистронезависимое.
    """
    return _PROMO_CODES.get(code.strip().upper())
