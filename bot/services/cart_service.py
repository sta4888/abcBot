import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import CartItem, Product
from bot.repositories.cart_repository import CartRepository
from bot.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AddToCartResult:
    """Результат добавления товара в корзину."""

    item: CartItem
    is_new: bool  # True — создана новая позиция, False — увеличено количество


@dataclass(frozen=True, slots=True)
class CartLine:
    """Одна строка корзины для отображения."""

    product: Product
    quantity: int
    line_total: int  # цена × количество, в копейках


@dataclass(frozen=True, slots=True)
class CartSummary:
    """Сводка всей корзины пользователя."""

    lines: list[CartLine]
    total: int  # общая сумма в копейках
    items_count: int  # суммарное количество штук

    @property
    def is_empty(self) -> bool:
        return not self.lines

    @property
    def total_rub(self) -> float:
        return self.total / 100


class CartService:
    """Фасад над работой с корзиной пользователя."""

    MAX_QUANTITY_PER_ITEM = 99

    def __init__(self, session: AsyncSession) -> None:
        self._cart_repo = CartRepository(session)
        self._product_repo = ProductRepository(session)

    async def add_item(self, user_id: int, product_id: int, quantity: int = 1) -> AddToCartResult | None:
        """Добавляет товар в корзину.

        Если товара нет в корзине — создаёт позицию.
        Если есть — увеличивает количество (ограничено MAX_QUANTITY_PER_ITEM).
        Если товар не найден/неактивен/нет в наличии — возвращает None.
        """
        product = await self._product_repo.get_by_id(product_id)
        if product is None or not product.is_in_stock:
            logger.info("Product %d not available for cart", product_id)
            return None

        existing = await self._cart_repo.get_by_user_and_product(user_id, product_id)
        if existing is not None:
            new_qty = min(existing.quantity + quantity, self.MAX_QUANTITY_PER_ITEM)
            await self._cart_repo.update_quantity(existing, new_qty)
            logger.info("Updated qty for user=%d product=%d: %d", user_id, product_id, new_qty)
            return AddToCartResult(item=existing, is_new=False)

        item = await self._cart_repo.create(
            user_id=user_id,
            product_id=product_id,
            quantity=min(quantity, self.MAX_QUANTITY_PER_ITEM),
        )
        logger.info("Added new item to cart user=%d product=%d", user_id, product_id)
        return AddToCartResult(item=item, is_new=True)

    async def get_summary(self, user_id: int) -> CartSummary:
        """Строит сводку корзины пользователя для отображения."""
        items = await self._cart_repo.list_by_user(user_id)

        lines: list[CartLine] = []
        total = 0
        items_count = 0
        for item in items:
            line_total = item.product.price * item.quantity
            lines.append(
                CartLine(
                    product=item.product,
                    quantity=item.quantity,
                    line_total=line_total,
                )
            )
            total += line_total
            items_count += item.quantity

        return CartSummary(lines=lines, total=total, items_count=items_count)

    async def change_quantity(self, user_id: int, product_id: int, delta: int) -> CartItem | None:
        """Меняет количество товара в корзине на delta (+1 или -1).

        Если после изменения quantity <= 0 — удаляет позицию.
        Возвращает обновлённую позицию или None, если удалили/не нашли.
        """
        item = await self._cart_repo.get_by_user_and_product(user_id, product_id)
        if item is None:
            return None

        new_qty = item.quantity + delta
        if new_qty <= 0:
            await self._cart_repo.delete(item)
            return None

        new_qty = min(new_qty, self.MAX_QUANTITY_PER_ITEM)
        await self._cart_repo.update_quantity(item, new_qty)
        return item

    async def remove_item(self, user_id: int, product_id: int) -> bool:
        """Удаляет товар из корзины. Возвращает True, если что-то удалили."""
        item = await self._cart_repo.get_by_user_and_product(user_id, product_id)
        if item is None:
            return False
        await self._cart_repo.delete(item)
        return True

    async def clear(self, user_id: int) -> None:
        """Очищает корзину."""
        await self._cart_repo.clear_user_cart(user_id)

    def render_text(self, summary: CartSummary) -> str:
        """Формирует текст корзины для показа в Telegram.

        Это форматирование, не бизнес-логика. Поэтому — обычная функция,
        не Builder, не паттерн. Builder появится для Order в следующей итерации.
        """
        if summary.is_empty:
            return "🛒 Твоя корзина пуста.\n\nЗагляни в каталог, выбери что-нибудь интересное."

        lines: list[str] = ["🛒 <b>Твоя корзина</b>", ""]
        for idx, line in enumerate(summary.lines, start=1):
            line_total_rub = line.line_total / 100
            lines.append(
                f"{idx}. <b>{line.product.name}</b>\n"
                f"   {line.product.price_rub:.2f}₽ × {line.quantity} "
                f"= <b>{line_total_rub:.2f}₽</b>"
            )

        lines.append("")
        lines.append("─" * 20)
        lines.append(f"<b>Итого:</b> {summary.total_rub:.2f}₽")
        lines.append(f"Товаров: <b>{summary.items_count}</b> шт.")

        return "\n".join(lines)

    async def get_items_count(self, user_id: int) -> int:
        """Сколько штук товаров в корзине пользователя.

        Если 0 — корзина пуста. Используется для UI: показывать ли кнопку 'Оформить'
        и какой счётчик в ней рисовать.
        """
        items = await self._cart_repo.list_by_user(user_id)
        return sum(item.quantity for item in items)
