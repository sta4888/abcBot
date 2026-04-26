from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Self, cast

from bot.models import Order, OrderItem
from bot.models.order import DELIVERY_METHODS, PAYMENT_METHODS

logger = logging.getLogger(__name__)


# ─── Ошибки билдера ───────────────────────────────────────────────


class OrderBuilderError(ValueError):
    """Базовая ошибка сборки заказа."""


class InvalidFieldError(OrderBuilderError):
    """Невалидное значение поля (адрес/телефон/метод и т.п.)."""


class IncompleteOrderError(OrderBuilderError):
    """В билдере не хватает обязательных полей для сборки."""


# ─── DTO для item-ов корзины, передаваемых в билдер ───────────────


@dataclass(frozen=True, slots=True)
class OrderItemSpec:
    """Спецификация позиции для будущего OrderItem.

    Билдер не знает про CartItem — он принимает абстрактные позиции.
    Это упрощает тестирование и развязывает слои.
    """

    product_id: int
    product_name: str
    price: int  # за штуку, в копейках
    quantity: int


# ─── Сам билдер ───────────────────────────────────────────────────


@dataclass
class OrderBuilder:
    """Накапливает данные заказа по шагам и собирает Order в build()."""

    user_id: int

    address: str | None = None
    delivery_method: str | None = None
    phone: str | None = None
    payment_method: str | None = None
    comment: str | None = None
    promo_code: str | None = None  # ← новое поле
    items: list[OrderItemSpec] = field(default_factory=list)

    # ─── Сеттеры с валидацией: возвращают self для цепочек ──────

    def set_address(self, address: str) -> Self:
        """Адрес доставки. Минимум 5 символов после strip."""
        cleaned = address.strip()
        if len(cleaned) < 5:
            raise InvalidFieldError("Адрес слишком короткий — нужно минимум 5 символов")
        if len(cleaned) > 500:
            raise InvalidFieldError("Адрес слишком длинный — не более 500 символов")
        self.address = cleaned
        return self

    def set_delivery_method(self, method: str) -> Self:
        """Способ доставки. Только из DELIVERY_METHODS."""
        if method not in DELIVERY_METHODS:
            raise InvalidFieldError(f"Неизвестный способ доставки: {method!r}")
        self.delivery_method = method
        return self

    def set_phone(self, phone: str) -> Self:
        """Контактный телефон. Принимаем форматы +7..., 8..., +380... и т.п.

        Базовая валидация: только цифры и + в начале, длина 10-15 цифр.
        Серьёзная валидация в проде делается через phonenumbers, но для MVP
        достаточно регулярки.
        """
        cleaned = phone.strip()
        # Сжимаем пробелы, дефисы, скобки
        digits = re.sub(r"[\s\-\(\)]", "", cleaned)
        # +X или X в начале, дальше только цифры
        if not re.fullmatch(r"\+?\d{10,15}", digits):
            raise InvalidFieldError("Телефон должен содержать 10-15 цифр, может начинаться с +")
        self.phone = digits
        return self

    def set_payment_method(self, method: str) -> Self:
        """Способ оплаты. Только из PAYMENT_METHODS."""
        if method not in PAYMENT_METHODS:
            raise InvalidFieldError(f"Неизвестный способ оплаты: {method!r}")
        self.payment_method = method
        return self

    def set_comment(self, comment: str | None) -> Self:
        """Комментарий к заказу. None или пустая строка — нет комментария."""
        if comment is None or not comment.strip():
            self.comment = None
            return self
        cleaned = comment.strip()
        if len(cleaned) > 1000:
            raise InvalidFieldError("Комментарий слишком длинный — не более 1000 символов")
        self.comment = cleaned
        return self

    def set_items(self, items: list[OrderItemSpec]) -> Self:
        """Позиции заказа из корзины."""
        if not items:
            raise InvalidFieldError("Корзина пуста — нечего заказывать")
        self.items = list(items)
        return self

    def set_promo_code(self, code: str | None) -> Self:
        """Устанавливает промокод. None / пустая строка — без промокода."""
        if code is None or not code.strip():
            self.promo_code = None
            return self
        cleaned = code.strip().upper()
        if len(cleaned) > 50:
            raise InvalidFieldError("Промокод слишком длинный")
        self.promo_code = cleaned
        return self

    # ─── Хелперы для отображения ───────────────────────────────

    @property
    def total(self) -> int:
        """Сумма заказа в копейках. Пересчитывается на лету."""
        return sum(item.price * item.quantity for item in self.items)

    def is_complete(self) -> bool:
        """Все ли обязательные поля заполнены?"""
        return all(
            (
                self.address,
                self.delivery_method,
                self.phone,
                self.payment_method,
                self.items,
            )
        )

    # ─── Финальная сборка ──────────────────────────────────────

    def build(self) -> Order:
        """Собирает Order с привязанными OrderItem-ами.

        Если каких-то обязательных полей не хватает — IncompleteOrderError.
        Order и OrderItem-ы НЕ сохраняются в БД здесь — это делает сервис,
        чтобы коммит был под управлением транзакции.
        """
        if not self.is_complete():
            raise IncompleteOrderError(
                "Не все поля заполнены. Нужны: адрес, доставка, телефон, оплата, минимум один товар."
            )

        # Mypy после is_complete() всё ещё считает поля Optional —
        # явный assert даёт narrowing.
        assert self.address is not None
        assert self.delivery_method is not None
        assert self.phone is not None
        assert self.payment_method is not None

        order = Order(
            user_id=self.user_id,
            delivery_method=self.delivery_method,
            delivery_address=self.address,
            contact_phone=self.phone,
            payment_method=self.payment_method,
            total=self.total,
            comment=self.comment,
        )
        for spec in self.items:
            order.items.append(
                OrderItem(
                    product_id=spec.product_id,
                    product_name=spec.product_name,
                    price=spec.price,
                    quantity=spec.quantity,
                )
            )
        logger.info(
            "Built Order for user=%d total=%.2f₽ items=%d",
            self.user_id,
            self.total / 100,
            len(self.items),
        )
        return order

    # ─── Сериализация в FSM-словарь и обратно ───────────────────

    def to_dict(self) -> dict[str, Any]:
        """Превращает билдер в словарь для FSM-state."""
        return {
            "user_id": self.user_id,
            "address": self.address,
            "delivery_method": self.delivery_method,
            "phone": self.phone,
            "payment_method": self.payment_method,
            "comment": self.comment,
            "promo_code": self.promo_code,
            "items": [
                {
                    "product_id": s.product_id,
                    "product_name": s.product_name,
                    "price": s.price,
                    "quantity": s.quantity,
                }
                for s in self.items
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Восстанавливает билдер из словаря FSM-state."""
        items_raw = cast(list[dict[str, Any]], data.get("items") or [])
        items = [
            OrderItemSpec(
                product_id=int(d["product_id"]),
                product_name=str(d["product_name"]),
                price=int(d["price"]),
                quantity=int(d["quantity"]),
            )
            for d in items_raw
        ]
        return cls(
            user_id=int(data["user_id"]),
            address=cast(str | None, data.get("address")),
            delivery_method=cast(str | None, data.get("delivery_method")),
            phone=cast(str | None, data.get("phone")),
            payment_method=cast(str | None, data.get("payment_method")),
            comment=cast(str | None, data.get("comment")),
            promo_code=cast(str | None, data.get("promo_code")),  # ← добавили
            items=items,
        )

        # ─── Рендер сводки для подтверждения ───────────────────────

    def render_summary(self, total_after_discounts: int | None = None) -> str:
        """Текст сводки заказа для шага подтверждения.

        Если total_after_discounts задан и отличается от base — показываем оба.
        """
        from bot.keyboards.user.checkout import DELIVERY_LABELS, PAYMENT_LABELS

        delivery_label = DELIVERY_LABELS.get(self.delivery_method or "", self.delivery_method or "—")
        payment_label = PAYMENT_LABELS.get(self.payment_method or "", self.payment_method or "—")

        lines: list[str] = ["📋 <b>Проверь данные заказа</b>", ""]
        lines.append("<b>Состав:</b>")
        for idx, item in enumerate(self.items, start=1):
            line_total_rub = (item.price * item.quantity) / 100
            lines.append(
                f"  {idx}. {item.product_name}\n"
                f"     {item.price / 100:.2f}₽ × {item.quantity} "
                f"= <b>{line_total_rub:.2f}₽</b>"
            )

        lines.append("")
        lines.append(f"<b>Адрес:</b> {self.address}")
        lines.append(f"<b>Доставка:</b> {delivery_label}")
        lines.append(f"<b>Телефон:</b> <code>{self.phone}</code>")
        lines.append(f"<b>Оплата:</b> {payment_label}")
        if self.comment:
            lines.append(f"<b>Комментарий:</b> {self.comment}")
        if self.promo_code:
            lines.append(f"<b>Промокод:</b> <code>{self.promo_code}</code>")

        lines.append("")
        base_total = self.total
        lines.append(f"<b>Базовая сумма:</b> {base_total / 100:.2f}₽")

        # Если задан итог после скидок и он отличается — показываем экономию
        if total_after_discounts is not None and total_after_discounts != base_total:
            saved = base_total - total_after_discounts
            lines.append(
                f"<b>После скидок:</b> {total_after_discounts / 100:.2f}₽ (сэкономлено: {saved / 100:.2f}₽) ✨"
            )

        lines.append(
            f"<b>Итого к оплате:</b> "
            f"{(total_after_discounts if total_after_discounts is not None else base_total) / 100:.2f}₽"
        )

        return "\n".join(lines)
