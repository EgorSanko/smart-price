"""API dependencies for dependency injection.

All dependencies are defined here for consistent usage across endpoints.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_maker


if TYPE_CHECKING:
    from app.services.product_service import ProductService


# === Database Dependencies ===


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    Yields:
        AsyncSession instance that auto-commits on success.

    Example:
        @router.get("/items")
        async def get_items(db: DbSession):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


# === Service Dependencies ===


async def get_product_service(
    session: AsyncSession = Depends(get_db),
) -> ProductService:
    """Get ProductService instance.

    Args:
        session: Database session from dependency.

    Returns:
        ProductService instance.
    """
    # Import here to avoid circular imports
    from app.services.product_service import ProductService

    return ProductService(session)


ProductServiceDep = Annotated["ProductService", Depends(get_product_service)]


# === Pagination Dependencies ===


class PaginationParams:
    """Common pagination parameters.

    Attributes:
        page: Page number (1-indexed).
        per_page: Items per page.
        offset: Calculated offset for SQL queries.
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(
            default=settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            description="Items per page",
        ),
    ) -> None:
        self.page = page
        self.per_page = per_page

    @property
    def offset(self) -> int:
        """Calculate SQL offset from page number."""
        return (self.page - 1) * self.per_page


PaginationDep = Annotated[PaginationParams, Depends()]


# === Filter Dependencies ===


class ProductFilterParams:
    """Common product filter parameters."""

    def __init__(
        self,
        marketplace_id: int | None = Query(
            None,
            gt=0,
            description="Filter by marketplace ID",
        ),
        category_id: int | None = Query(
            None,
            gt=0,
            description="Filter by category ID",
        ),
        min_price: float | None = Query(
            None,
            ge=0,
            description="Minimum price",
        ),
        max_price: float | None = Query(
            None,
            ge=0,
            description="Maximum price",
        ),
        in_stock: bool = Query(
            True,
            description="Only show available products",
        ),
        brand: str | None = Query(
            None,
            max_length=255,
            description="Filter by brand name",
        ),
    ) -> None:
        self.marketplace_id = marketplace_id
        self.category_id = category_id
        self.min_price = min_price
        self.max_price = max_price
        self.in_stock = in_stock
        self.brand = brand


ProductFilterDep = Annotated[ProductFilterParams, Depends()]
