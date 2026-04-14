"""CheaperSearch model — tracks a "Найти дешевле" task end-to-end."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CheaperStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheaperSearch(Base, TimestampMixin):
    """One user request "найди дешевле на этот товар".

    Populated progressively by the Playwright worker (Phase 3):
    - PENDING: row created, task queued
    - RUNNING: worker picked up, planned_shops set from first json_rephrase_items frame
    - COMPLETED: offers array final
    - FAILED: error set (captcha, timeout, Alisa down, etc.)
    """

    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
        comment="Public task id (UUID) used in WS/polling URLs",
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="Product URL pasted by user",
    )

    orig_domain: Mapped[str | None] = mapped_column(String(200), nullable=True)

    status: Mapped[CheaperStatus] = mapped_column(
        SQLEnum(
            CheaperStatus,
            name="cheaper_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=CheaperStatus.PENDING,
    )

    product_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_img_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    orig_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True, default="RUR")

    planned_shops: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="[{domain: 'ozon.ru'}, ...] — first json_rephrase_items from Alisa",
    )

    offers: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="[{domain, price, productName, url, imgUrl, rating, reviewCnt}, ...] sorted by price",
    )

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_cheaper_searches_user_created", "user_id", "created_at"),
        Index("ix_cheaper_searches_status", "status"),
    )

    def mark_running(self) -> None:
        self.status = CheaperStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def mark_completed(self) -> None:
        self.status = CheaperStatus.COMPLETED
        self.finished_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        self.status = CheaperStatus.FAILED
        self.error = error
        self.finished_at = datetime.now(UTC)
