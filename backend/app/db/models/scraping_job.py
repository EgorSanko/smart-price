"""Scraping job model for tracking marketplace search tasks."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapingJob(Base, TimestampMixin):
    """Tracks individual scraping tasks across marketplaces.

    Records query, marketplace, status, results count, and timing
    for analytics and debugging.

    Attributes:
        query: Search query text.
        marketplace: Target marketplace name.
        status: Current job status.
        results_count: Number of products found.
        duration_ms: Execution time in milliseconds.
        error: Error message if failed.
        metadata_json: Additional job metadata (region, filters, etc).
        started_at: When scraping actually began.
        finished_at: When scraping completed or failed.
    """

    query: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Search query text",
    )

    marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Target marketplace (onliner, yandex, wildberries, ozon)",
    )

    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.PENDING,
        comment="Current job status",
    )

    results_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of products found",
    )

    duration_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Execution time in milliseconds",
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if job failed",
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata (region, filters, user agent)",
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When scraping started",
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When scraping completed or failed",
    )

    __table_args__ = (
        Index("ix_scraping_jobs_marketplace_status", "marketplace", "status"),
        Index("ix_scraping_jobs_created_desc", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"ScrapingJob(id={self.id}, query={self.query!r}, "
            f"marketplace={self.marketplace!r}, status={self.status!r})"
        )

    def mark_running(self) -> None:
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def mark_completed(self, results_count: int, duration_ms: float) -> None:
        """Mark job as completed with results."""
        self.status = JobStatus.COMPLETED
        self.results_count = results_count
        self.duration_ms = duration_ms
        self.finished_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        """Mark job as failed with error."""
        self.status = JobStatus.FAILED
        self.error = error
        self.finished_at = datetime.now(UTC)
