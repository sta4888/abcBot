from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base

if TYPE_CHECKING:
    from bot.models.product import Product
    from bot.models.user import User


class CartItem(Base):
    """Один позиция в корзине пользователя.

    Уникальное сочетание (user_id, product_id) — не бывает двух строк
    одного и того же товара у одного юзера. При повторном добавлении
    инкрементим quantity.
    """

    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_items_user_product"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Отношения
    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()

    def __repr__(self) -> str:
        return f"<CartItem id={self.id} user_id={self.user_id} product_id={self.product_id} qty={self.quantity}>"
