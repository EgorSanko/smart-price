"""Category model with hierarchical structure."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.db.models.product import Product


class Category(Base, TimestampMixin):
    """Product category with hierarchical structure.

    Supports parent-child relationships for nested categories.

    Attributes:
        name: Category name (e.g., "Смартфоны").
        slug: URL-friendly identifier (e.g., "smartphones").
        parent_id: ID of parent category (None for root categories).
        level: Depth in hierarchy (0 for root, 1 for first level children, etc.).
        description: Optional category description.

    Example:
        Электроника (level=0)
        └── Телефоны (level=1)
            └── Смартфоны (level=2)
    """

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Category name",
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly identifier",
    )

    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent category ID (NULL for root categories)",
    )

    level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Depth in hierarchy (0 = root)",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description",
    )

    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Lucide icon name for frontend",
    )

    citilink_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Path on citilink.ru for this category",
    )

    # Self-referential relationships
    parent: Mapped[Category | None] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
        lazy="joined",
    )

    children: Mapped[list[Category]] = relationship(
        "Category",
        back_populates="parent",
        lazy="selectin",
    )

    # Products in this category
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name={self.name!r}, level={self.level})"

    @property
    def full_path(self) -> str:
        """Get full category path (e.g., 'Электроника > Телефоны > Смартфоны')."""
        parts = [self.name]
        current = self.parent
        while current:
            parts.insert(0, current.name)
            current = current.parent
        return " > ".join(parts)
