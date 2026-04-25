from datetime import datetime
from decimal import Decimal  # noqa: F401  # на случай будущей эволюции, не используем
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base

if TYPE_CHECKING:
    from bot.models.user import User

# Допустимые статусы заказа. В itr.6 заменим на полноценный State.
ORDER_STATUSES = ("new", "paid", "shipped", "delivered", "cancelled")
DELIVERY_METHODS = ("courier", "pickup", "post")
PAYMENT_METHODS = ("fake", "yookassa", "stripe")  # пока поддержим только fake


class Order(Base):
    """Заголовок заказа: кто, что в общем, статус, итог."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            f"status IN {ORDER_STATUSES}",
            name="ck_orders_status",
        ),
        CheckConstraint(
            f"delivery_method IN {DELIVERY_METHODS}",
            name="ck_orders_delivery_method",
        ),
        CheckConstraint(
            f"payment_method IN {PAYMENT_METHODS}",
            name="ck_orders_payment_method",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="new",
        server_default="new",
        index=True,
    )

    # Доставка
    delivery_method: Mapped[str] = mapped_column(String(20))
    delivery_address: Mapped[str] = mapped_column(Text)

    # Контакты
    contact_phone: Mapped[str] = mapped_column(String(32))

    # Оплата
    payment_method: Mapped[str] = mapped_column(String(20))

    # Итог в копейках, копируется при создании
    total: Mapped[int] = mapped_column(Integer)

    # Опциональный комментарий пользователя
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Связи
    user: Mapped["User"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",  # сразу подгружаем позиции при загрузке заказа
    )

    @property
    def total_rub(self) -> float:
        return self.total / 100

    def __repr__(self) -> str:
        return f"<Order id={self.id} user_id={self.user_id} status={self.status!r} total={self.total_rub:.2f}₽>"


class OrderItem(Base):
    """Позиция заказа. Имя и цена товара зафиксированы на момент создания."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
    )

    # Ссылка на товар. ondelete=SET NULL — если товар удалят, позиция остаётся,
    # но теряет ссылку. Имя и цена при этом сохраняются в order_items.
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Снимок названия и цены на момент заказа
    product_name: Mapped[str] = mapped_column(String(200))
    price: Mapped[int] = mapped_column(Integer)  # в копейках, цена за штуку
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped["Order"] = relationship(back_populates="items")

    @property
    def line_total(self) -> int:
        """Сумма этой позиции в копейках."""
        return self.price * self.quantity

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} name={self.product_name!r} price={self.price / 100:.2f}₽ qty={self.quantity}>"
