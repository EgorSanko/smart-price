"""User model for authentication and personalization."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.db.models.alert import PriceAlert, SearchHistory


class User(Base, TimestampMixin):
    """User account model.

    Stores user credentials and profile information.
    Supports both email/password and OAuth authentication.

    Attributes:
        email: User's email address (unique).
        hashed_password: Bcrypt-hashed password (null for OAuth users).
        is_active: Whether the account is active.
        is_verified: Whether email has been verified.
        is_superuser: Admin privileges.
        full_name: User's display name.
        avatar_url: Profile picture URL.
        oauth_provider: OAuth provider name (google, yandex, etc.).
        oauth_id: User ID from OAuth provider.
        last_login_at: Last login timestamp.

    Security:
        - Passwords are hashed using bcrypt
        - Email verification required for sensitive operations
        - OAuth users have null password
    """

    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email (unique)",
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Bcrypt-hashed password (null for OAuth)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Account active status",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email verification status",
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Admin privileges",
    )

    # Profile
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Display name",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Profile picture URL",
    )

    # OAuth
    oauth_provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="OAuth provider: google, yandex, etc.",
    )

    oauth_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="User ID from OAuth provider",
    )

    # Subscription
    subscription_plan: Mapped[str] = mapped_column(
        String(20),
        default="free",
        server_default="free",
        nullable=False,
        comment="Subscription: free, pro, business",
    )

    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When subscription expires",
    )

    is_test_account: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="YooKassa test reviewer account",
    )

    # Activity tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last login timestamp",
    )

    # Relationships
    price_alerts: Mapped[list[PriceAlert]] = relationship(
        "PriceAlert",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    search_history: Mapped[list[SearchHistory]] = relationship(
        "SearchHistory",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email!r}, is_active={self.is_active})"

    @property
    def has_active_subscription(self) -> bool:
        """Check if user has an active paid subscription."""
        if self.subscription_plan == "free":
            return False
        if self.is_test_account:
            return True
        if self.subscription_expires_at is None:
            return False
        return self.subscription_expires_at > datetime.now(UTC)

    @property
    def is_oauth_user(self) -> bool:
        """Check if user registered via OAuth."""
        return self.oauth_provider is not None

    @property
    def display_name(self) -> str:
        """Get display name or email prefix."""
        if self.full_name:
            return self.full_name
        return self.email.split("@")[0]

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.now(UTC)
