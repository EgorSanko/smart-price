"""Price alerts and search history models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.db.models.product import Product
    from app.db.models.user import User


class AlertType(str, Enum):
    """Types of price alerts."""

    BELOW = "below"  # Price drops below target
    DROP_PERCENT = "drop_percent"  # Price drops by X%
    ANY_CHANGE = "any_change"  # Any price change


class AlertStatus(str, Enum):
    """Status of price alert."""

    ACTIVE = "active"  # Monitoring
    TRIGGERED = "triggered"  # Alert fired
    EXPIRED = "expired"  # Manually disabled or expired
    PAUSED = "paused"  # Temporarily paused


class PriceAlert(Base, TimestampMixin):
    """Price alert for a product.

    Notifies user when price conditions are met.

    Attributes:
        user_id: Owner of the alert.
        product_id: Product being monitored.
        target_price: Target price threshold.
        alert_type: Type of alert (below, drop_percent, any_change).
        status: Current alert status.
        triggered_at: When alert was triggered.
        triggered_price: Price when alert was triggered.
        notification_sent: Whether notification was sent.

    Example:
        Alert: "Notify me when iPhone 15 drops below 80,000 RUB"
        - alert_type = "below"
        - target_price = 80000
    """

    __tablename__ = "price_alerts"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Alert owner",
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Product being monitored",
    )

    target_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Target price threshold",
    )

    alert_type: Mapped[AlertType] = mapped_column(
        SQLEnum(AlertType, name="alert_type_enum"),
        nullable=False,
        default=AlertType.BELOW,
        comment="Type of alert",
    )

    status: Mapped[AlertStatus] = mapped_column(
        SQLEnum(AlertStatus, name="alert_status_enum"),
        nullable=False,
        default=AlertStatus.ACTIVE,
        index=True,
        comment="Current status",
    )

    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When alert was triggered",
    )

    triggered_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Price when triggered",
    )

    notification_sent: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Notification delivery status",
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="price_alerts",
        lazy="joined",
    )

    product: Mapped[Product] = relationship(
        "Product",
        back_populates="alerts",
        lazy="joined",
    )

    __table_args__ = (
        # Index for checking active alerts
        Index(
            "ix_price_alert_active",
            "status",
            "product_id",
        ),
        # Index for user's alerts
        Index(
            "ix_price_alert_user_status",
            "user_id",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"PriceAlert(id={self.id}, "
            f"user_id={self.user_id}, "
            f"product_id={self.product_id}, "
            f"target={self.target_price}, "
            f"status={self.status.value})"
        )

    @property
    def is_active(self) -> bool:
        """Check if alert is actively monitoring."""
        return self.status == AlertStatus.ACTIVE

    def trigger(self, current_price: Decimal) -> None:
        """Mark alert as triggered."""
        self.status = AlertStatus.TRIGGERED
        self.triggered_at = func.now()
        self.triggered_price = current_price

    def check_condition(self, current_price: Decimal) -> bool:
        """Check if alert condition is met.

        Args:
            current_price: Current product price.

        Returns:
            True if alert should be triggered.
        """
        if self.alert_type == AlertType.BELOW:
            return current_price <= self.target_price
        elif self.alert_type == AlertType.DROP_PERCENT:
            # target_price here represents percentage drop
            # Need original price from somewhere (product.original_price?)
            return False  # Implement with original price reference
        elif self.alert_type == AlertType.ANY_CHANGE:
            # Need previous price to compare
            return True  # Simplified
        return False


class SearchHistory(Base):
    """User's search history.

    Tracks searches for analytics and personalization.

    Attributes:
        user_id: User who performed search (null for anonymous).
        query: Search query string.
        filters: Applied filters as JSON.
        results_count: Number of results returned.
        session_id: Anonymous session identifier.
        clicked_product_id: Product clicked from results (if any).
    """

    __tablename__ = "search_history"

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who searched (null for anonymous)",
    )

    query: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Search query",
    )

    filters: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Applied filters",
    )

    results_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of results",
    )

    session_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Session identifier for anonymous users",
    )

    clicked_product_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        comment="Product clicked from results",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped[User | None] = relationship(
        "User",
        back_populates="search_history",
        lazy="joined",
    )

    clicked_product: Mapped[Product | None] = relationship(
        "Product",
        lazy="joined",
    )

    __table_args__ = (
        # Index for analytics queries
        Index(
            "ix_search_history_created_at_desc",
            created_at.desc(),
        ),
        # Index for user's history
        Index(
            "ix_search_history_user_created",
            "user_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"SearchHistory(id={self.id}, "
            f"query={self.query!r}, "
            f"results={self.results_count})"
        )
