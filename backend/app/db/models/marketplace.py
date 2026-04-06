"""Marketplace model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.db.models.product import Product


class Marketplace(Base, TimestampMixin):
    """Marketplace model (Ozon, Wildberries, etc.).

    Attributes:
        name: Short unique name (e.g., "ozon", "wildberries").
        display_name: Human-readable name (e.g., "Ozon", "Wildberries").
        base_url: Base URL of the marketplace.
        is_active: Whether scraping is enabled for this marketplace.
        config: JSON configuration for the scraper (selectors, rate limits, etc.).
        description: Optional description.
    """

    # Override auto-generated tablename
    __tablename__ = "marketplaces"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Short unique name: ozon, wildberries, yandex_market",
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable name for UI",
    )

    base_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Base URL of the marketplace",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether scraping is enabled",
    )

    config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="Scraper configuration (rate_limit, selectors, etc.)",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description",
    )

    # Relationships
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="marketplace",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Marketplace(id={self.id}, name={self.name!r}, is_active={self.is_active})"
