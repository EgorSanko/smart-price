"""Health check endpoints.

Provides basic liveness and readiness probes for container orchestration.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str
    timestamp: datetime
    version: str


class ReadinessResponse(BaseModel):
    """Readiness check response with dependency status."""
    
    status: str
    timestamp: datetime
    version: str
    checks: dict[str, Any]


@router.get(
    "",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Simple liveness probe that returns OK if the service is running.",
)
async def health_check() -> HealthResponse:
    """Basic health check endpoint.
    
    Returns:
        HealthResponse with status "healthy".
        
    Example:
        GET /api/v1/health
        {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Checks connectivity to all dependencies (database, etc.).",
    responses={
        503: {"description": "One or more dependencies are unavailable"},
    },
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> ReadinessResponse:
    """Readiness check with dependency verification.
    
    Checks:
        - PostgreSQL connection
        
    Returns:
        ReadinessResponse with status of each dependency.
        
    Raises:
        HTTPException: 503 if any dependency is unavailable.
    """
    checks: dict[str, Any] = {}
    all_healthy = True
    
    # Check PostgreSQL
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["postgres"] = {"status": "healthy", "latency_ms": None}
    except Exception as e:
        checks["postgres"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False
    
    # TODO: Add Redis check
    # TODO: Add Qdrant check
    # TODO: Add ClickHouse check
    
    response = ReadinessResponse(
        status="healthy" if all_healthy else "unhealthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        checks=checks,
    )
    
    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.model_dump(),
        )
    
    return response


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Kubernetes liveness probe - returns OK if the process is running.",
)
async def liveness_probe() -> HealthResponse:
    """Kubernetes liveness probe.
    
    This should always return OK if the process is running.
    It does NOT check dependencies.
    
    Returns:
        HealthResponse with status "alive".
    """
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
    )
