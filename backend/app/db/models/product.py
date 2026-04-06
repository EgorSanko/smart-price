"""Product model — core entity of the system."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.db.models.alert import PriceAlert
    from app.db.models.category import Category
    from app.db.models.marketplace import Marketplace
    from app.db.models.price_history import PriceHistory
    from app.db.models.product_match import ProductMatch


class Product(Base, TimestampMixin):
    """Product from a marketplace.

    Central entity storing product information scraped from marketplaces.

    Attributes:
        external_id: Product ID on the marketplace (SKU).
        marketplace_id: Reference to the marketplace.
        title: Product title/name.
        description: Full product description.
        brand: Brand name.
        category_id: Reference to product category.
        current_price: Current price in RUB.
        original_price: Price before discount (if any).
        currency: Currency code (default: RUB).
        url: Direct URL to product page.
        image_url: Main product image URL.
        images: List of all product image URLs.
        rating: Average rating (0-5).
        reviews_count: Number of reviews.
        specs: Product specifications as JSON.
        is_available: Whether product is in stock.
        seller_name: Name of the seller.
        seller_rating: Seller's rating.
        barcode: Product barcode (EAN/UPC) for matching.
        last_scraped_at: Timestamp of last successful scrape.
    """

    __tablename__ = "products"

    # Marketplace reference
    external_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Product ID on the marketplace",
    )

    marketplace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("marketplaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to marketplace",
    )

    # Basic info
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Product title",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full product description",
    )

    brand: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Brand name",
    )

    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to category",
    )

    # Pricing
    current_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Current price in currency",
    )

    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Price before discount",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="RUB",
        nullable=False,
        comment="Currency code (ISO 4217)",
    )

    # URLs and images
    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="Direct URL to product page",
    )

    image_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="Main product image URL",
    )

    images: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(1000)),
        nullable=True,
        comment="List of all product image URLs",
    )

    # Ratings
    rating: Mapped[float | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="Average rating (0.00-5.00)",
    )

    reviews_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of reviews",
    )

    # Additional data
    specs: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Product specifications as JSON",
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether product is in stock",
    )

    # Seller info
    seller_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Seller name",
    )

    seller_rating: Mapped[float | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="Seller rating",
    )

    # For product matching
    barcode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Product barcode (EAN/UPC)",
    )

    # Scraping metadata
    last_scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful scrape",
    )

    # Relationships
    marketplace: Mapped[Marketplace] = relationship(
        "Marketplace",
        back_populates="products",
        lazy="joined",
    )

    category: Mapped[Category | None] = relationship(
        "Category",
        back_populates="products",
        lazy="joined",
    )

    price_history: Mapped[list[PriceHistory]] = relationship(
        "PriceHistory",
        back_populates="product",
        lazy="selectin",
        order_by="desc(PriceHistory.recorded_at)",
    )

    # Product matching relationships
    canonical_matches: Mapped[list[ProductMatch]] = relationship(
        "ProductMatch",
        foreign_keys="ProductMatch.canonical_product_id",
        back_populates="canonical",
        lazy="selectin",
    )

    matched_by: Mapped[list[ProductMatch]] = relationship(
        "ProductMatch",
        foreign_keys="ProductMatch.matched_product_id",
        back_populates="matched",
        lazy="selectin",
    )

    # Price alerts for this product
    alerts: Mapped[list[PriceAlert]] = relationship(
        "PriceAlert",
        back_populates="product",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        # Unique constraint: one product per marketplace
        Index(
            "ix_product_marketplace_external",
            "marketplace_id",
            "external_id",
            unique=True,
        ),
        # Full-text search index (requires pg_trgm extension)
        Index(
            "ix_product_title_gin",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
        # Composite index for common queries
        Index(
            "ix_product_available_price",
            "is_available",
            "current_price",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"Product(id={self.id}, "
            f"external_id={self.external_id!r}, "
            f"title={self.title[:30]!r}...)"
        )

    @property
    def discount_percent(self) -> float | None:
        """Calculate discount percentage if original_price exists."""
        if self.original_price and self.original_price > self.current_price:
            discount = (1 - self.current_price / self.original_price) * 100
            return round(float(discount), 1)
        return None

    @property
    def has_discount(self) -> bool:
        """Check if product has a discount."""
        return self.discount_percent is not None and self.discount_percent > 0
