"""Pydantic schemas module.

This module exports all schema classes used for API request/response
validation and serialization.
"""

from app.schemas.product import (
    # Enums
    AlertType,
    PriceTrend,
    SortOrder,
    # Base schemas
    ProductBase,
    ProductCreate,
    ProductUpdate,
    # Response schemas
    MarketplaceInfo,
    MatchedProduct,
    PriceAlertCreate,
    PriceAlertResponse,
    PriceHistoryResponse,
    PricePoint,
    PriceStats,
    ProductComparison,
    ProductDetail,
    ProductInDB,
    ProductListItem,
    ProductListResponse,
    ProductResponse,
    ProductSearchResult,
    ProductWithPriceHistory,
    # Search schemas
    SearchFacets,
    SearchFilters,
)

__all__ = [
    # Enums
    "SortOrder",
    "PriceTrend",
    "AlertType",
    # Product schemas
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductInDB",
    "ProductResponse",
    "ProductListItem",
    "ProductListResponse",
    "ProductDetail",
    "ProductWithPriceHistory",
    # Price schemas
    "PricePoint",
    "PriceStats",
    "PriceHistoryResponse",
    # Search schemas
    "SearchFilters",
    "SearchFacets",
    "ProductSearchResult",
    # Comparison schemas
    "MatchedProduct",
    "ProductComparison",
    # Alert schemas
    "PriceAlertCreate",
    "PriceAlertResponse",
    # Marketplace
    "MarketplaceInfo",
]
