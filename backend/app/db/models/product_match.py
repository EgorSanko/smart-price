"""Product matching model for cross-marketplace product linking."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.product import Product


class ProductMatch(Base):
    """Links identical products across different marketplaces.

    Enables price comparison for the same product on Ozon, Wildberries, etc.

    Attributes:
        canonical_product_id: The "main" product (oldest or most complete).
        matched_product_id: The matched product from another marketplace.
        confidence_score: ML model confidence (0.0 - 1.0).
        match_method: How the match was established (ml, barcode, manual).
        verified: Whether a human has verified this match.
        verified_at: When the match was verified.
        verified_by: Who verified the match (user_id or "system").

    Example:
        Product A (Ozon, iPhone 15) <-> Product B (Wildberries, iPhone 15)
        canonical_product_id = A.id
        matched_product_id = B.id
        confidence_score = 0.95
        match_method = "ml"
    """

    __tablename__ = "product_matches"

    canonical_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Main/canonical product ID",
    )

    matched_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Matched product ID",
    )

    confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Match confidence (0.0000 - 1.0000)",
    )

    match_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ml",
        comment="Method: ml, barcode, title_similarity, manual",
    )

    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Human verification status",
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When verified",
    )

    verified_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who verified (user_id or 'system')",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    canonical: Mapped[Product] = relationship(
        "Product",
        foreign_keys=[canonical_product_id],
        back_populates="canonical_matches",
        lazy="joined",
    )

    matched: Mapped[Product] = relationship(
        "Product",
        foreign_keys=[matched_product_id],
        back_populates="matched_by",
        lazy="joined",
    )

    __table_args__ = (
        # Ensure no duplicate matches
        UniqueConstraint(
            "canonical_product_id",
            "matched_product_id",
            name="uq_product_match_pair",
        ),
        # Index for finding all matches for a product
        Index(
            "ix_product_match_canonical",
            "canonical_product_id",
        ),
        Index(
            "ix_product_match_matched",
            "matched_product_id",
        ),
        # Index for filtering by confidence
        Index(
            "ix_product_match_confidence",
            "confidence_score",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"ProductMatch(id={self.id}, "
            f"canonical={self.canonical_product_id}, "
            f"matched={self.matched_product_id}, "
            f"confidence={self.confidence_score:.2f})"
        )

    @property
    def is_high_confidence(self) -> bool:
        """Check if match has high confidence (>= 0.9)."""
        return float(self.confidence_score) >= 0.9

    @property
    def is_reliable(self) -> bool:
        """Check if match is reliable (verified or high confidence)."""
        return self.verified or self.is_high_confidence
