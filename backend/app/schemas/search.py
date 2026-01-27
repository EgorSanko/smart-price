"""Pydantic schemas for Search endpoints."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas.product import ProductResponse


class SortOrder(str, Enum):
    """Available sort options for search results."""
    
    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    RATING = "rating"
    REVIEWS = "reviews"
    NEWEST = "newest"


class SearchType(str, Enum):
    """Search algorithm type."""
    
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchQuery(BaseModel):
    """Search query parameters."""
    
    q: str = Field(..., min_length=1, max_length=500, description="Search query")
    marketplace_ids: list[int] | None = Field(
        None,
        description="Filter by marketplace IDs",
    )
    category_ids: list[int] | None = Field(
        None,
        description="Filter by category IDs",
    )
    min_price: float | None = Field(None, ge=0, description="Minimum price")
    max_price: float | None = Field(None, ge=0, description="Maximum price")
    in_stock_only: bool = Field(True, description="Only show available products")
    brands: list[str] | None = Field(None, description="Filter by brand names")
    min_rating: float | None = Field(
        None,
        ge=0,
        le=5,
        description="Minimum rating",
    )
    
    sort_by: SortOrder = Field(SortOrder.RELEVANCE, description="Sort order")
    search_type: SearchType = Field(SearchType.HYBRID, description="Search algorithm")
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")


class PriceFacet(BaseModel):
    """Price range facet for filtering."""
    
    min_price: float
    max_price: float
    avg_price: float
    median_price: float | None = None


class MarketplaceFacet(BaseModel):
    """Marketplace facet with count."""
    
    id: int
    name: str
    display_name: str
    count: int


class CategoryFacet(BaseModel):
    """Category facet with count."""
    
    id: int
    name: str
    slug: str
    count: int


class BrandFacet(BaseModel):
    """Brand facet with count."""
    
    name: str
    count: int


class SearchFacets(BaseModel):
    """Aggregated facets for search filters."""
    
    price: PriceFacet | None = None
    marketplaces: list[MarketplaceFacet] = []
    categories: list[CategoryFacet] = []
    brands: list[BrandFacet] = []


class SearchResult(BaseModel):
    """Single search result with relevance score."""
    
    product: dict  # Will be ProductResponse, using dict to avoid circular import
    score: float = Field(..., ge=0, description="Relevance score")
    highlights: dict[str, list[str]] | None = Field(
        None,
        description="Highlighted text fragments",
    )
    
    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Paginated search results with facets."""
    
    items: list[SearchResult]
    total: int
    page: int
    per_page: int
    pages: int
    query: str
    facets: SearchFacets | None = None
    search_type: SearchType


class SearchSuggestion(BaseModel):
    """Search autocomplete suggestion."""
    
    text: str
    type: str = Field(
        ...,
        description="Suggestion type: 'query', 'brand', 'category'",
    )
    count: int | None = Field(None, description="Number of matching products")


class SearchSuggestionsResponse(BaseModel):
    """Autocomplete suggestions response."""
    
    suggestions: list[SearchSuggestion]
    query: str
