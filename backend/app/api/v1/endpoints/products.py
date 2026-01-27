"""Product CRUD endpoints.

Provides REST API for product management and retrieval.
"""

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.api.v1.deps import (
    PaginationDep,
    ProductFilterDep,
    ProductServiceDep,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    ProductWithPriceHistory,
)


router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List products",
    description="Get paginated list of products with optional filtering.",
)
async def list_products(
    service: ProductServiceDep,
    pagination: PaginationDep,
    filters: ProductFilterDep,
) -> ProductListResponse:
    """List products with filtering and pagination.

    Args:
        service: Product service dependency.
        pagination: Pagination parameters.
        filters: Filter parameters.

    Returns:
        Paginated list of products.

    Example:
        GET /api/v1/products?page=1&per_page=20&min_price=100
    """
    products, total = await service.list_products(
        marketplace_id=filters.marketplace_id,
        category_id=filters.category_id,
        is_available=filters.in_stock,
        min_price=filters.min_price,
        max_price=filters.max_price,
        brand=filters.brand,
        page=pagination.page,
        per_page=pagination.per_page,
    )

    pages = (total + pagination.per_page - 1) // pagination.per_page

    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pages,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    responses={
        404: {"description": "Product not found"},
    },
)
async def get_product(
    service: ProductServiceDep,
    product_id: int = Path(..., gt=0, description="Product ID"),
) -> ProductResponse:
    """Get single product by ID.

    Args:
        service: Product service dependency.
        product_id: Product primary key.

    Returns:
        Product details.

    Raises:
        HTTPException: 404 if product not found.
    """
    product = await service.get_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    return ProductResponse.model_validate(product)


@router.get(
    "/{product_id}/history",
    response_model=ProductWithPriceHistory,
    summary="Get product with price history",
    responses={
        404: {"description": "Product not found"},
    },
)
async def get_product_with_history(
    service: ProductServiceDep,
    product_id: int = Path(..., gt=0, description="Product ID"),
    days: int = Query(30, ge=1, le=365, description="Days of history"),
) -> ProductWithPriceHistory:
    """Get product with price history and statistics.

    Args:
        service: Product service dependency.
        product_id: Product primary key.
        days: Number of days of price history to include.

    Returns:
        Product with price history and statistics.

    Raises:
        HTTPException: 404 if product not found.
    """
    result = await service.get_with_price_history(product_id, days=days)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    return result


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    responses={
        400: {"description": "Validation error"},
    },
)
async def create_product(
    service: ProductServiceDep,
    data: ProductCreate,
) -> ProductResponse:
    """Create a new product.

    Args:
        service: Product service dependency.
        data: Product creation data.

    Returns:
        Created product.

    Raises:
        HTTPException: 400 if validation fails.
    """
    try:
        product = await service.create(data)
        return ProductResponse.model_validate(product)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
    responses={
        404: {"description": "Product not found"},
    },
)
async def update_product(
    service: ProductServiceDep,
    data: ProductUpdate,
    product_id: int = Path(..., gt=0, description="Product ID"),
) -> ProductResponse:
    """Update an existing product.

    Args:
        service: Product service dependency.
        data: Product update data (partial).
        product_id: Product primary key.

    Returns:
        Updated product.

    Raises:
        HTTPException: 404 if product not found.
    """
    try:
        product = await service.update(product_id, data)
        return ProductResponse.model_validate(product)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    responses={
        404: {"description": "Product not found"},
    },
)
async def delete_product(
    service: ProductServiceDep,
    product_id: int = Path(..., gt=0, description="Product ID"),
) -> None:
    """Delete a product.

    Args:
        service: Product service dependency.
        product_id: Product primary key.

    Raises:
        HTTPException: 404 if product not found.
    """
    try:
        await service.delete(product_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e


@router.post(
    "/upsert",
    response_model=ProductResponse,
    summary="Create or update product",
    description="Upsert product by marketplace_id + external_id combination.",
)
async def upsert_product(
    service: ProductServiceDep,
    data: ProductCreate,
) -> ProductResponse:
    """Create or update product by external identifier.

    If a product with the same marketplace_id and external_id exists,
    it will be updated. Otherwise, a new product is created.

    Args:
        service: Product service dependency.
        data: Product data.

    Returns:
        Created or updated product.
    """
    try:
        product = await service.upsert(data)
        return ProductResponse.model_validate(product)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
