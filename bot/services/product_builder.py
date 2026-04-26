import logging
from dataclasses import dataclass
from typing import Self

logger = logging.getLogger(__name__)


class ProductBuilderError(ValueError):
    """Ошибка сборки товара."""


@dataclass(frozen=True, slots=True)
class ProductSpec:
    """Готовая спецификация для создания товара."""

    category_id: int
    name: str
    description: str
    price: int  # в копейках
    stock: int
    image_file_id: str | None


@dataclass
class ProductBuilder:
    """Накапливает данные нового товара по шагам админского FSM."""

    category_id: int

    name: str | None = None
    description: str | None = None
    price: int | None = None  # копейки
    stock: int | None = None
    image_file_id: str | None = None

    def set_name(self, name: str) -> Self:
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ProductBuilderError("Название слишком короткое (минимум 2 символа)")
        if len(cleaned) > 200:
            raise ProductBuilderError("Название слишком длинное (>200)")
        self.name = cleaned
        return self

    def set_description(self, description: str) -> Self:
        cleaned = description.strip()
        if len(cleaned) < 1:
            raise ProductBuilderError("Описание не может быть пустым")
        self.description = cleaned
        return self

    def set_price_rub(self, price_rub: str) -> Self:
        """Принимает цену в рублях строкой (как ввёл пользователь).

        Конвертирует в копейки. Кидает ошибку, если формат невалидный.
        """
        try:
            value = float(price_rub.replace(",", ".").strip())
        except ValueError as e:
            raise ProductBuilderError("Цена должна быть числом (например: 199 или 149.99)") from e
        if value <= 0:
            raise ProductBuilderError("Цена должна быть больше нуля")
        if value > 1_000_000:
            raise ProductBuilderError("Цена слишком большая")
        self.price = round(value * 100)
        return self

    def set_stock(self, stock_str: str) -> Self:
        try:
            value = int(stock_str.strip())
        except ValueError as e:
            raise ProductBuilderError("Остаток должен быть целым числом") from e
        if value < 0:
            raise ProductBuilderError("Остаток не может быть отрицательным")
        if value > 1_000_000:
            raise ProductBuilderError("Остаток слишком большой")
        self.stock = value
        return self

    def set_image(self, file_id: str | None) -> Self:
        self.image_file_id = file_id
        return self

    def is_complete(self) -> bool:
        return all(
            (
                self.name,
                self.description,
                self.price is not None,
                self.stock is not None,
            )
        )

    def build(self) -> ProductSpec:
        if not self.is_complete():
            raise ProductBuilderError("Не все поля заполнены: имя, описание, цена, остаток обязательны")

        assert self.name is not None
        assert self.description is not None
        assert self.price is not None
        assert self.stock is not None

        return ProductSpec(
            category_id=self.category_id,
            name=self.name,
            description=self.description,
            price=self.price,
            stock=self.stock,
            image_file_id=self.image_file_id,
        )
