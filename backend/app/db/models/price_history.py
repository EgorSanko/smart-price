"""Price history model for tracking price changes."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.product import Product


class PriceHistory(Base):
    """Historical price records for products.

    Stores price snapshots taken during scraping.
    Used for price trend analysis, charts, and forecasting.

    Attributes:
        product_id: Reference to the product.
        price: Price at the time of recording.
        original_price: Original price (before discount) at the time.
        currency: Currency code.
        recorded_at: When this price was recorded.

    Note:
        This table can grow large. Consider partitioning by recorded_at
        or moving old data to ClickHouse for analytics.
    """

    __tablename__ = "price_history"

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to product",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Price at the time of recording",
    )

    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Original price before discount",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="RUB",
        nullable=False,
        comment="Currency code",
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When this price was recorded",
    )

    # Relationships
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="price_history",
        lazy="joined",
    )

    # Indexes for time-series queries
    __table_args__ = (
        # Composite index for querying price history by product and date
        Index(
            "ix_price_history_product_date",
            "product_id",
            "recorded_at",
        ),
        # Index for finding recent prices
        Index(
            "ix_price_history_recorded_at_desc",
            recorded_at.desc(),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"PriceHistory(id={self.id}, "
            f"product_id={self.product_id}, "
            f"price={self.price}, "
            f"recorded_at={self.recorded_at})"
        )

    @property
    def discount_percent(self) -> float | None:
        """Calculate discount percentage at the time of recording."""
        if self.original_price and self.original_price > self.price:
            discount = (1 - self.price / self.original_price) * 100
            return round(float(discount), 1)
        return None
