import pytest

from bot.services.product_builder import (
    ProductBuilder,
    ProductBuilderError,
)


def test_full_flow() -> None:
    spec = (
        ProductBuilder(category_id=1)
        .set_name("Test product")
        .set_description("Хорошая штука")
        .set_price_rub("199.99")
        .set_stock("10")
        .set_image("file_id_xxx")
        .build()
    )
    assert spec.category_id == 1
    assert spec.name == "Test product"
    assert spec.price == 19999  # копейки
    assert spec.stock == 10
    assert spec.image_file_id == "file_id_xxx"


def test_price_with_comma() -> None:
    builder = ProductBuilder(category_id=1).set_price_rub("199,99")
    assert builder.price == 19999


def test_negative_price_rejected() -> None:
    with pytest.raises(ProductBuilderError):
        ProductBuilder(category_id=1).set_price_rub("-100")


def test_zero_price_rejected() -> None:
    with pytest.raises(ProductBuilderError):
        ProductBuilder(category_id=1).set_price_rub("0")


def test_invalid_price_format() -> None:
    with pytest.raises(ProductBuilderError):
        ProductBuilder(category_id=1).set_price_rub("free!")


def test_negative_stock_rejected() -> None:
    with pytest.raises(ProductBuilderError):
        ProductBuilder(category_id=1).set_stock("-5")


def test_short_name_rejected() -> None:
    with pytest.raises(ProductBuilderError):
        ProductBuilder(category_id=1).set_name("a")


def test_build_without_required_fields() -> None:
    with pytest.raises(ProductBuilderError, match="Не все поля"):
        ProductBuilder(category_id=1).build()


def test_image_can_be_none() -> None:
    spec = (
        ProductBuilder(category_id=1)
        .set_name("Без фото")
        .set_description("ok")
        .set_price_rub("100")
        .set_stock("1")
        .set_image(None)
        .build()
    )
    assert spec.image_file_id is None
