"""Product schemas for API and internal use.

This module defines Pydantic models for product data validation
and serialization throughout the application.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class SortOrder(str, Enum):
    """Sort order for product listings."""

    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    RATING = "rating"
    REVIEWS = "reviews"
    NEWEST = "newest"


class PriceTrend(str, Enum):
    """Price trend direction."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


# ============================================================================
# Base Schemas
# ============================================================================


class ProductBase(BaseModel):
    """Base product schema with common fields."""

    title: str = Field(..., min_length=1, max_length=500, description="Product title")
    brand: str | None = Field(None, max_length=255, description="Brand name")
    description: str | None = Field(None, max_length=10000, description="Product description")

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Clean and normalize title."""
        return " ".join(v.split())  # Normalize whitespace


class ProductCreate(ProductBase):
    """Schema for creating a new product (from scraper)."""

    external_id: str = Field(..., min_length=1, max_length=100, description="ID on marketplace")
    marketplace_id: int = Field(..., gt=0, description="Marketplace database ID")
    url: str = Field(..., min_length=1, max_length=1000, description="Product URL")

    current_price: float = Field(..., gt=0, description="Current price")
    original_price: float | None = Field(None, gt=0, description="Price before discount")
    currency: str = Field("RUB", max_length=3, description="Currency code")

    image_url: str | None = Field(None, max_length=1000, description="Main image URL")
    images: list[str] = Field(default_factory=list, description="Additional image URLs")

    rating: float | None = Field(None, ge=0, le=5, description="Product rating (0-5)")
    reviews_count: int = Field(0, ge=0, description="Number of reviews")

    is_available: bool = Field(True, description="Product availability")
    seller_name: str | None = Field(None, max_length=255, description="Seller name")
    seller_rating: float | None = Field(None, ge=0, le=5, description="Seller rating")

    specs: dict[str, Any] = Field(default_factory=dict, description="Product specifications")

    @field_validator("external_id")
    @classmethod
    def clean_external_id(cls, v: str) -> str:
        """Strip whitespace from external ID."""
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL has scheme."""
        if not v.startswith(("http://", "https://")):
            return f"https://{v}"
        return v

    @model_validator(mode="after")
    def validate_prices(self) -> "ProductCreate":
        """Ensure original_price > current_price if set."""
        if self.original_price and self.original_price <= self.current_price:
            self.original_price = None
        return self

    model_config = ConfigDict(str_strip_whitespace=True)


class ProductUpdate(BaseModel):
    """Schema for updating product fields."""

    title: str | None = Field(None, min_length=1, max_length=500)
    brand: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=10000)
    current_price: float | None = Field(None, gt=0)
    original_price: float | None = Field(None, gt=0)
    image_url: str | None = Field(None, max_length=1000)
    is_available: bool | None = None
    seller_name: str | None = Field(None, max_length=255)
    specs: dict[str, Any] | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


# ============================================================================
# Response Schemas
# ============================================================================


class MarketplaceInfo(BaseModel):
    """Marketplace information embedded in product response."""

    id: int
    name: str
    base_url: str

    model_config = ConfigDict(from_attributes=True)


class ProductInDB(ProductBase):
    """Product schema as stored in database."""

    id: int
    external_id: str
    marketplace_id: int

    current_price: float
    original_price: float | None
    currency: str
    url: str
    image_url: str | None
    images: list[str]

    rating: float | None
    reviews_count: int
    is_available: bool
    seller_name: str | None
    seller_rating: float | None

    specs: dict[str, Any]

    created_at: datetime
    updated_at: datetime
    last_scraped_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(ProductInDB):
    """Full product response with marketplace info."""

    marketplace: MarketplaceInfo | None = None
    discount_percent: float | None = None

    @model_validator(mode="after")
    def calculate_discount(self) -> "ProductResponse":
        """Calculate discount percentage."""
        if self.original_price and self.original_price > self.current_price:
            self.discount_percent = round(
                (1 - self.current_price / self.original_price) * 100, 1
            )
        return self


class ProductListItem(BaseModel):
    """Minimal product info for list views."""

    id: int
    title: str
    brand: str | None
    current_price: float
    original_price: float | None
    image_url: str | None
    rating: float | None
    reviews_count: int
    marketplace_id: int
    marketplace_name: str | None = None
    url: str
    is_available: bool
    discount_percent: float | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Price History Schemas
# ============================================================================


class PricePoint(BaseModel):
    """Single price point in history."""

    price: float
    original_price: float | None = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceStats(BaseModel):
    """Price statistics for a product."""

    min_price: float = Field(..., description="Historical minimum price")
    max_price: float = Field(..., description="Historical maximum price")
    avg_price: float = Field(..., description="Average price")
    current_price: float = Field(..., description="Current price")
    current_vs_min_percent: float = Field(
        ..., description="How much current price is above minimum (%)"
    )
    trend: PriceTrend = Field(..., description="Price trend direction")
    data_points: int = Field(..., description="Number of price records")

    @classmethod
    def from_prices(cls, prices: list[float], current: float) -> "PriceStats":
        """Create stats from price list.

        Args:
            prices: List of historical prices.
            current: Current price.

        Returns:
            Calculated price statistics.
        """
        if not prices:
            return cls(
                min_price=current,
                max_price=current,
                avg_price=current,
                current_price=current,
                current_vs_min_percent=0.0,
                trend=PriceTrend.STABLE,
                data_points=1,
            )

        min_p = min(prices)
        max_p = max(prices)
        avg_p = sum(prices) / len(prices)

        # Calculate trend from recent prices
        if len(prices) >= 3:
            recent = prices[-3:]
            if recent[-1] > recent[0] * 1.02:
                trend = PriceTrend.RISING
            elif recent[-1] < recent[0] * 0.98:
                trend = PriceTrend.FALLING
            else:
                trend = PriceTrend.STABLE
        else:
            trend = PriceTrend.STABLE

        current_vs_min = ((current - min_p) / min_p * 100) if min_p > 0 else 0

        return cls(
            min_price=min_p,
            max_price=max_p,
            avg_price=round(avg_p, 2),
            current_price=current,
            current_vs_min_percent=round(current_vs_min, 1),
            trend=trend,
            data_points=len(prices),
        )


class ProductWithPriceHistory(ProductResponse):
    """Product with full price history and statistics."""

    price_history: list[PricePoint] = Field(default_factory=list)
    price_stats: PriceStats | None = None


# ============================================================================
# Search & Comparison Schemas
# ============================================================================


class SearchFilters(BaseModel):
    """Search filters."""

    q: str = Field(..., min_length=1, description="Search query")
    marketplace_ids: list[int] | None = Field(None, description="Filter by marketplaces")
    min_price: Annotated[float | None, Field(ge=0)] = None
    max_price: Annotated[float | None, Field(ge=0)] = None
    in_stock_only: bool = Field(True, description="Only available products")
    min_rating: Annotated[float | None, Field(ge=0, le=5)] = None
    brands: list[str] | None = None
    sort: SortOrder = Field(SortOrder.RELEVANCE, description="Sort order")


class SearchFacets(BaseModel):
    """Search result facets for filtering."""

    marketplaces: dict[str, int] = Field(
        default_factory=dict, description="Count by marketplace"
    )
    brands: dict[str, int] = Field(default_factory=dict, description="Count by brand")
    price_range: dict[str, float] = Field(
        default_factory=dict, description="min_price, max_price, avg_price"
    )


class ProductSearchResult(BaseModel):
    """Paginated search results."""

    products: list[ProductListItem]
    total: int = Field(..., ge=0, description="Total matching products")
    page: int = Field(..., ge=1, description="Current page")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=0, description="Total pages")
    facets: SearchFacets | None = None

    @model_validator(mode="after")
    def calculate_pages(self) -> "ProductSearchResult":
        """Calculate total pages."""
        self.pages = (self.total + self.per_page - 1) // self.per_page if self.total > 0 else 0
        return self


class MatchedProduct(BaseModel):
    """Product match from another marketplace."""

    product: ProductListItem
    marketplace_name: str
    confidence_score: float = Field(..., ge=0, le=1, description="Match confidence")
    price_difference: float = Field(..., description="Price difference from canonical")
    price_difference_percent: float = Field(..., description="Price difference %")


class ProductComparison(BaseModel):
    """Comparison of same product across marketplaces."""

    canonical_title: str
    brand: str | None
    canonical_product_id: int
    matches: list[MatchedProduct]
    best_price: MatchedProduct | None
    worst_price: MatchedProduct | None
    price_spread: float = Field(..., description="Max price - Min price")
    price_spread_percent: float = Field(..., description="Price spread as %")


# ============================================================================
# Alert Schemas
# ============================================================================


class AlertType(str, Enum):
    """Type of price alert."""

    BELOW = "below"  # Price drops below target
    DROP_PERCENT = "drop_percent"  # Price drops by X%
    ANY_CHANGE = "any_change"  # Any price change


class PriceAlertCreate(BaseModel):
    """Schema for creating price alert."""

    product_id: int = Field(..., gt=0)
    target_price: float | None = Field(None, gt=0, description="Target price (for BELOW type)")
    drop_percent: float | None = Field(
        None, gt=0, le=100, description="Drop percentage (for DROP_PERCENT type)"
    )
    alert_type: AlertType = Field(AlertType.BELOW)

    @model_validator(mode="after")
    def validate_alert_params(self) -> "PriceAlertCreate":
        """Ensure required params are set based on alert type."""
        if self.alert_type == AlertType.BELOW and not self.target_price:
            raise ValueError("target_price required for BELOW alert type")
        if self.alert_type == AlertType.DROP_PERCENT and not self.drop_percent:
            raise ValueError("drop_percent required for DROP_PERCENT alert type")
        return self


class PriceAlertResponse(BaseModel):
    """Price alert response."""

    id: int
    user_id: int
    product_id: int
    product_title: str
    current_price: float
    target_price: float | None
    drop_percent: float | None
    alert_type: AlertType
    is_active: bool
    created_at: datetime
    triggered_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Response Aliases (for API compatibility)
# ============================================================================


class ProductListResponse(BaseModel):
    """Paginated list of products response."""

    items: list[ProductListItem]
    total: int = Field(..., ge=0, description="Total items count")
    page: int = Field(1, ge=1, description="Current page")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    pages: int = Field(0, ge=0, description="Total pages count")

    @model_validator(mode="after")
    def calculate_pages(self) -> "ProductListResponse":
        """Calculate total pages."""
        if self.per_page > 0:
            self.pages = (self.total + self.per_page - 1) // self.per_page
        return self

    model_config = ConfigDict(from_attributes=True)


class ProductDetail(ProductWithPriceHistory):
    """Detailed product response (alias for ProductWithPriceHistory)."""

    pass


class PriceHistoryResponse(BaseModel):
    """Price history response for a product."""

    product_id: int
    product_title: str
    current_price: float
    history: list[PricePoint]
    stats: PriceStats | None = None

    model_config = ConfigDict(from_attributes=True)
