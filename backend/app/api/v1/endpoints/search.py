"""Search endpoints.

Provides product search functionality with full-text and semantic search.
"""

from fastapi import APIRouter, Query

from app.api.v1.deps import DbSession, PaginationDep
from app.schemas.search import (
    SearchQuery,
    SearchResponse,
    SearchSuggestionsResponse,
    SearchType,
    SortOrder,
)
from app.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search products",
    description="Search products across all marketplaces with filtering and sorting.",
)
async def search_products(
    db: DbSession,
    pagination: PaginationDep,
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    marketplace_id: list[int] | None = Query(
        None,
        description="Filter by marketplace IDs",
    ),
    category_id: list[int] | None = Query(
        None,
        description="Filter by category IDs",
    ),
    min_price: float | None = Query(None, ge=0, description="Minimum price"),
    max_price: float | None = Query(None, ge=0, description="Maximum price"),
    in_stock: bool = Query(True, description="Only show available products"),
    brand: list[str] | None = Query(None, description="Filter by brands"),
    min_rating: float | None = Query(None, ge=0, le=5, description="Minimum rating"),
    sort: SortOrder = Query(SortOrder.RELEVANCE, description="Sort order"),
    search_type: SearchType = Query(SearchType.KEYWORD, description="Search algorithm"),
) -> SearchResponse:
    """Search products with full-text search.

    Supports multiple search algorithms:
    - **keyword**: PostgreSQL full-text search (fast, exact matching)
    - **semantic**: Vector similarity search via Qdrant (understanding meaning)
    - **hybrid**: Combination of both (best results, slower)

    Args:
        db: Database session.
        pagination: Pagination parameters.
        q: Search query string.
        marketplace_id: Filter by marketplace IDs.
        category_id: Filter by category IDs.
        min_price: Minimum price filter.
        max_price: Maximum price filter.
        in_stock: Only return available products.
        brand: Filter by brand names.
        min_rating: Minimum product rating.
        sort: Sort order for results.
        search_type: Search algorithm to use.

    Returns:
        Paginated search results with facets.

    Example:
        GET /api/v1/search?q=iphone&min_price=50000&sort=price_asc
    """
    # Build search query
    query = SearchQuery(
        q=q,
        marketplace_ids=marketplace_id,
        category_ids=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock,
        brands=brand,
        min_rating=min_rating,
        sort_by=sort,
        search_type=search_type,
        page=pagination.page,
        per_page=pagination.per_page,
    )

    # Execute search
    service = SearchService(db)
    results, total, facets = await service.search(query)

    # Calculate pages
    pages = (total + pagination.per_page - 1) // pagination.per_page

    return SearchResponse(
        items=results,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pages,
        query=q,
        facets=facets,
        search_type=search_type,
    )


@router.get(
    "/suggest",
    response_model=SearchSuggestionsResponse,
    summary="Search suggestions",
    description="Get autocomplete suggestions for search query.",
)
async def search_suggestions(
    db: DbSession,
    q: str = Query(..., min_length=2, max_length=100, description="Partial query"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions"),
) -> SearchSuggestionsResponse:
    """Get search autocomplete suggestions.

    Returns suggestions based on:
    - Popular search queries
    - Matching product titles
    - Matching brand names
    - Matching category names

    Args:
        db: Database session.
        q: Partial search query (min 2 characters).
        limit: Maximum number of suggestions.

    Returns:
        List of search suggestions.

    Example:
        GET /api/v1/search/suggest?q=iph
        -> ["iPhone 15", "iPhone 14", "iPhone case", ...]
    """
    service = SearchService(db)
    suggestions = await service.get_suggestions(q, limit=limit)

    return SearchSuggestionsResponse(
        suggestions=suggestions,
        query=q,
    )


@router.post(
    "/image",
    response_model=SearchResponse,
    summary="Search by image",
    description="Find similar products by uploading an image (CLIP-based).",
)
async def search_by_image(
    db: DbSession,
    pagination: PaginationDep,
    # image: UploadFile = File(..., description="Product image"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    marketplace_id: list[int] | None = Query(None),
) -> SearchResponse:
    """Search products by image similarity.

    Uses CLIP model to encode the image and find visually similar products
    in the vector database.

    Args:
        db: Database session.
        pagination: Pagination parameters.
        image: Uploaded product image (JPEG, PNG).
        min_price: Minimum price filter.
        max_price: Maximum price filter.
        marketplace_id: Filter by marketplace IDs.

    Returns:
        Products visually similar to the uploaded image.

    Note:
        This endpoint is a placeholder. Image search will be implemented
        in Sprint 9 with CLIP integration.
    """
    # TODO: Implement in Sprint 9
    # 1. Validate image format
    # 2. Encode image with CLIP
    # 3. Search Qdrant for similar vectors
    # 4. Return matched products

    return SearchResponse(
        items=[],
        total=0,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=0,
        query="[image search]",
        facets=None,
        search_type=SearchType.SEMANTIC,
    )
