from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Page[T]:
    """Одна страница списка объектов."""

    items: list[T]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        """Общее количество страниц."""
        if self.page_size <= 0:
            return 0
        return max(1, (self.total + self.page_size - 1) // self.page_size)

    @property
    def has_next(self) -> bool:
        """Есть ли следующая страница."""
        return self.page + 1 < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Есть ли предыдущая страница."""
        return self.page > 0

    @property
    def offset(self) -> int:
        """OFFSET для SQL-запроса."""
        return self.page * self.page_size
