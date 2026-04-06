"""FastAPI application entry point.

This module creates and configures the FastAPI application instance.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import AppException
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Handles startup and shutdown events:
    - Startup: Create database tables (dev only)
    - Shutdown: Dispose database connections

    Args:
        app: FastAPI application instance.

    Yields:
        None during application lifetime.
    """
    # Startup: always create tables (safe — does nothing if they exist)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed test account for YooKassa reviewers
    await _seed_test_account()

    yield

    # Shutdown
    from app.scrapers.playwright_scrapers import close_browser

    await close_browser()
    await engine.dispose()


def create_application() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered price comparison across marketplaces",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        return JSONResponse(
            status_code=_get_status_code(exc),
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        """Root endpoint redirect to docs."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


def _get_status_code(exc: AppException) -> int:
    """Map exception code to HTTP status code."""
    mapping = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "RATE_LIMIT_ERROR": status.HTTP_429_TOO_MANY_REQUESTS,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
    }
    return mapping.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def _seed_test_account():
    """Create permanent test account for YooKassa review."""
    from datetime import datetime

    from sqlalchemy import select

    from app.core.security import hash_password
    from app.db.models.user import User
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == "test@smartprice.ru"))
        if result.scalar_one_or_none():
            return  # already exists

        user = User(
            email="test@smartprice.ru",
            hashed_password=hash_password("TestPass123"),
            full_name="Тестовый Пользователь",
            is_active=True,
            is_verified=True,
            is_test_account=True,
            subscription_plan="pro",
            subscription_expires_at=datetime(2030, 1, 1, tzinfo=UTC),
        )
        session.add(user)
        await session.commit()


# Create application instance
app = create_application()
