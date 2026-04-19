from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base

if TYPE_CHECKING:
    from bot.models.category import Category


class Product(Base):
    """Товар каталога. Цена хранится в копейках (минорных единицах)."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Категория — обязательна для товара
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    # Цена в копейках: 199.99 руб = 19999
    price: Mapped[int] = mapped_column(Integer)

    # Telegram file_id для фото. None — если ещё не загружено админом
    image_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Сколько на складе. 0 = нет в наличии
    stock: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Прямая связь: product.category
    category: Mapped["Category"] = relationship(back_populates="products")

    @property
    def price_rub(self) -> float:
        """Цена в рублях — для отображения пользователю."""
        return self.price / 100

    @property
    def is_in_stock(self) -> bool:
        """В наличии, если активен и есть остаток."""
        return self.is_active and self.stock > 0

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} price={self.price_rub:.2f}₽ stock={self.stock}>"
