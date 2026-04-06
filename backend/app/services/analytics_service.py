"""Analytics service — scraping job tracking and search statistics."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scraping_job import JobStatus, ScrapingJob


class AnalyticsService:
    """Service for tracking scraping jobs and generating analytics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(
        self,
        query: str,
        marketplace: str,
        metadata: dict | None = None,
    ) -> ScrapingJob:
        """Create a new scraping job record."""
        job = ScrapingJob(
            query=query,
            marketplace=marketplace,
            status=JobStatus.PENDING,
            metadata_json=metadata,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def complete_job(
        self,
        job_id: int,
        results_count: int,
        duration_ms: float,
    ) -> None:
        """Mark a scraping job as completed."""
        job = await self.session.get(ScrapingJob, job_id)
        if job:
            job.mark_completed(results_count, duration_ms)
            await self.session.flush()

    async def fail_job(self, job_id: int, error: str) -> None:
        """Mark a scraping job as failed."""
        job = await self.session.get(ScrapingJob, job_id)
        if job:
            job.mark_failed(error)
            await self.session.flush()

    async def get_stats(self, days: int = 7) -> dict:
        """Get scraping statistics for the given period."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total jobs
        total = (
            await self.session.scalar(
                select(func.count(ScrapingJob.id)).where(ScrapingJob.created_at >= since)
            )
            or 0
        )

        # By status
        status_stmt = (
            select(ScrapingJob.status, func.count(ScrapingJob.id))
            .where(ScrapingJob.created_at >= since)
            .group_by(ScrapingJob.status)
        )
        status_result = await self.session.execute(status_stmt)
        by_status = {row[0].value: row[1] for row in status_result}

        # By marketplace
        mp_stmt = (
            select(ScrapingJob.marketplace, func.count(ScrapingJob.id))
            .where(ScrapingJob.created_at >= since)
            .group_by(ScrapingJob.marketplace)
        )
        mp_result = await self.session.execute(mp_stmt)
        by_marketplace = {row[0]: row[1] for row in mp_result}

        # Avg duration
        avg_duration = await self.session.scalar(
            select(func.avg(ScrapingJob.duration_ms))
            .where(ScrapingJob.created_at >= since)
            .where(ScrapingJob.status == JobStatus.COMPLETED)
        )

        # Avg results
        avg_results = await self.session.scalar(
            select(func.avg(ScrapingJob.results_count))
            .where(ScrapingJob.created_at >= since)
            .where(ScrapingJob.status == JobStatus.COMPLETED)
        )

        # Top queries
        top_queries_stmt = (
            select(ScrapingJob.query, func.count(ScrapingJob.id).label("cnt"))
            .where(ScrapingJob.created_at >= since)
            .group_by(ScrapingJob.query)
            .order_by(func.count(ScrapingJob.id).desc())
            .limit(10)
        )
        top_result = await self.session.execute(top_queries_stmt)
        top_queries = [{"query": row[0], "count": row[1]} for row in top_result]

        return {
            "period_days": days,
            "total_jobs": total,
            "by_status": by_status,
            "by_marketplace": by_marketplace,
            "avg_duration_ms": round(avg_duration, 1) if avg_duration else None,
            "avg_results_count": round(avg_results, 1) if avg_results else None,
            "top_queries": top_queries,
            "success_rate": round(by_status.get("completed", 0) / total * 100, 1)
            if total > 0
            else None,
        }
