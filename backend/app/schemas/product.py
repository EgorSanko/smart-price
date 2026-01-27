"""Pydantic schemas for Product endpoints.

Schemas are organized by purpose:
- Base: Common fields
- Create: Input for creation
- Update: Input for updates (partial)
- InDB: Full model representation
- Response: API response format
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


# === Base Schemas ===


class ProductBase(BaseModel):
    """Base product schema with common fields."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    brand: str | None = Field(None, max_length=255)


class MarketplaceInfo(BaseModel):
    """Marketplace information embedded in product response."""

    id: int
    name: str
    display_name: str

    model_config = ConfigDict(from_attributes=True)


class CategoryInfo(BaseModel):
    """Category information embedded in product response."""

    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


# === Create Schemas ===


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    external_id: str = Field(..., min_length=1, max_length=100)
    marketplace_id: int = Field(..., gt=0)
    category_id: int | None = Field(None, gt=0)

    current_price: float = Field(..., gt=0)
    original_price: float | None = Field(None, gt=0)
    currency: str = Field("RUB", max_length=3)

    url: HttpUrl
    image_url: HttpUrl | None = None
    images: list[HttpUrl] | None = None

    rating: float | None = Field(None, ge=0, le=5)
    reviews_count: int = Field(0, ge=0)

    specs: dict | None = None

    is_available: bool = True
    seller_name: str | None = Field(None, max_length=255)
    seller_rating: float | None = Field(None, ge=0, le=5)

    @field_validator("external_id")
    @classmethod
    def clean_external_id(cls, v: str) -> str:
        """Remove whitespace from external_id."""
        return v.strip()

    @field_validator("url", "image_url", mode="before")
    @classmethod
    def convert_url_to_string(cls, v: HttpUrl | str | None) -> str | None:
        """Convert HttpUrl to string for database storage."""
        if v is None:
            return None
        return str(v)


class ProductUpdate(BaseModel):
    """Schema for updating an existing product (partial update)."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    brand: str | None = Field(None, max_length=255)
    category_id: int | None = Field(None, gt=0)

    current_price: float | None = Field(None, gt=0)
    original_price: float | None = Field(None, gt=0)

    image_url: HttpUrl | None = None

    rating: float | None = Field(None, ge=0, le=5)
    reviews_count: int | None = Field(None, ge=0)

    is_available: bool | None = None
    seller_name: str | None = Field(None, max_length=255)
    seller_rating: float | None = Field(None, ge=0, le=5)


# === Response Schemas ===


class ProductInDB(ProductBase):
    """Full product representation from database."""

    id: int
    external_id: str
    marketplace_id: int
    category_id: int | None

    current_price: float
    original_price: float | None
    currency: str
    discount_percent: float | None = None

    url: str
    image_url: str | None
    images: list[str] | None

    rating: float | None
    reviews_count: int

    specs: dict | None

    is_available: bool
    seller_name: str | None
    seller_rating: float | None

    created_at: datetime
    updated_at: datetime
    last_scraped_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(ProductInDB):
    """Product response with nested marketplace and category info."""

    marketplace: MarketplaceInfo | None = None
    category: CategoryInfo | None = None


class ProductListResponse(BaseModel):
    """Paginated list of products."""

    items: list[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int


# === Price History Schemas ===


class PricePoint(BaseModel):
    """Single price point in history."""

    price: float
    original_price: float | None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceStats(BaseModel):
    """Aggregated price statistics."""

    min_price: float
    max_price: float
    avg_price: float
    current_price: float
    current_vs_min_percent: float = Field(
        ...,
        description="How much current price is above minimum (%)",
    )
    trend: str = Field(
        ...,
        description="Price trend: 'rising', 'falling', or 'stable'",
    )

    @field_validator("trend")
    @classmethod
    def validate_trend(cls, v: str) -> str:
        allowed = {"rising", "falling", "stable"}
        if v not in allowed:
            raise ValueError(f"trend must be one of {allowed}")
        return v


class ProductWithPriceHistory(ProductResponse):
    """Product with full price history and statistics."""

    price_history: list[PricePoint] = []
    price_stats: PriceStats | None = None


# === Comparison Schemas ===


class MatchedProduct(BaseModel):
    """Product match from another marketplace."""

    product: ProductResponse
    marketplace_name: str
    confidence_score: float = Field(..., ge=0, le=1)


class ProductComparison(BaseModel):
    """Comparison of the same product across marketplaces."""

    canonical_title: str
    brand: str | None
    matches: list[MatchedProduct]
    best_price: MatchedProduct
    price_difference_percent: float = Field(
        ...,
        description="Price difference between cheapest and most expensive (%)",
    )
