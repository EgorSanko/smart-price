"""Payment model for YooKassa integration."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Payment(Base, TimestampMixin):
    """Records every YooKassa payment transaction."""

    __tablename__ = "payments"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    yookassa_payment_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="YooKassa payment UUID",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount in RUB",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="RUB",
        server_default="RUB",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
        comment="pending, succeeded, canceled",
    )
    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="pro or business",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user = relationship("User", backref="payments", lazy="selectin")
