import pytest

from bot.services.order_builder import (
    IncompleteOrderError,
    InvalidFieldError,
    OrderBuilder,
    OrderItemSpec,
)


@pytest.fixture
def sample_items() -> list[OrderItemSpec]:
    return [
        OrderItemSpec(product_id=1, product_name="Книга", price=29900, quantity=2),
        OrderItemSpec(product_id=2, product_name="Ручка", price=10000, quantity=1),
    ]


def test_builder_full_flow(sample_items: list[OrderItemSpec]) -> None:
    builder = OrderBuilder(user_id=42)
    builder.set_items(sample_items)
    builder.set_address("г. Москва, ул. Тверская 7")
    builder.set_delivery_method("courier")
    builder.set_phone("+7 999 123 45 67")
    builder.set_payment_method("fake")
    builder.set_comment("Позвонить за час")

    order = builder.build()

    assert order.user_id == 42
    assert order.delivery_method == "courier"
    assert order.contact_phone == "+79991234567"  # очищен от пробелов
    assert order.total == 29900 * 2 + 10000  # 69800 копеек
    assert len(order.items) == 2


def test_builder_chaining(sample_items: list[OrderItemSpec]) -> None:
    """Сеттеры возвращают self — можно цепочкой."""
    order = (
        OrderBuilder(user_id=1)
        .set_items(sample_items)
        .set_address("Адрес тестовый")
        .set_delivery_method("pickup")
        .set_phone("89991234567")
        .set_payment_method("fake")
        .build()
    )
    assert order.delivery_method == "pickup"


def test_short_address_rejected() -> None:
    builder = OrderBuilder(user_id=1)
    with pytest.raises(InvalidFieldError, match="Адрес слишком короткий"):
        builder.set_address("xy")


def test_invalid_delivery_method() -> None:
    builder = OrderBuilder(user_id=1)
    with pytest.raises(InvalidFieldError, match="Неизвестный способ доставки"):
        builder.set_delivery_method("teleport")


def test_phone_validation() -> None:
    builder = OrderBuilder(user_id=1)
    builder.set_phone("89991234567")
    assert builder.phone == "89991234567"

    builder.set_phone("+7 (999) 123-45-67")
    assert builder.phone == "+79991234567"

    with pytest.raises(InvalidFieldError):
        builder.set_phone("abcde")
    with pytest.raises(InvalidFieldError):
        builder.set_phone("123")  # слишком короткий


def test_build_incomplete_raises(sample_items: list[OrderItemSpec]) -> None:
    builder = OrderBuilder(user_id=1)
    builder.set_items(sample_items)
    builder.set_address("Адрес тестовый")
    # Не хватает: delivery, phone, payment

    with pytest.raises(IncompleteOrderError):
        builder.build()


def test_serialization_roundtrip(sample_items: list[OrderItemSpec]) -> None:
    """to_dict → from_dict восстанавливает все данные."""
    original = (
        OrderBuilder(user_id=1)
        .set_items(sample_items)
        .set_address("Адрес тестовый")
        .set_delivery_method("post")
        .set_phone("+79991234567")
        .set_payment_method("fake")
        .set_comment("Спасибо")
    )
    data = original.to_dict()
    restored = OrderBuilder.from_dict(data)

    assert restored.user_id == original.user_id
    assert restored.address == original.address
    assert restored.delivery_method == original.delivery_method
    assert restored.phone == original.phone
    assert restored.payment_method == original.payment_method
    assert restored.comment == original.comment
    assert restored.items == original.items


def test_total_calculation(sample_items: list[OrderItemSpec]) -> None:
    builder = OrderBuilder(user_id=1)
    builder.set_items(sample_items)
    # 29900 * 2 + 10000 * 1 = 69800
    assert builder.total == 69800
