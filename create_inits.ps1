# Smart Price - Create __init__.py files with proper exports
# Run from smart-price folder

$ErrorActionPreference = "Stop"
Write-Host "Creating __init__.py files..." -ForegroundColor Cyan

# backend/app/__init__.py
$content = @'
"""Smart Price application."""
'@
Set-Content -Path "backend/app/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/__init__.py" -ForegroundColor Green

# backend/app/core/__init__.py
$content = @'
"""Core utilities and exceptions."""

from app.core.exceptions import (
    AppException,
    NotFoundError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
)
'@
Set-Content -Path "backend/app/core/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/core/__init__.py" -ForegroundColor Green

# backend/app/api/__init__.py
$content = @'
"""API package."""
'@
Set-Content -Path "backend/app/api/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/api/__init__.py" -ForegroundColor Green

# backend/app/api/v1/__init__.py
$content = @'
"""API v1 package."""

from app.api.v1.router import router
'@
Set-Content -Path "backend/app/api/v1/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/api/v1/__init__.py" -ForegroundColor Green

# backend/app/api/v1/endpoints/__init__.py
$content = @'
"""API v1 endpoints."""
'@
Set-Content -Path "backend/app/api/v1/endpoints/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/api/v1/endpoints/__init__.py" -ForegroundColor Green

# backend/app/db/__init__.py
$content = @'
"""Database package."""

from app.db.base import Base
from app.db.session import async_session_maker, get_async_session
'@
Set-Content -Path "backend/app/db/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/db/__init__.py" -ForegroundColor Green

# backend/app/db/models/__init__.py
$content = @'
"""Database models."""

from app.db.models.marketplace import Marketplace
from app.db.models.category import Category
from app.db.models.product import Product
from app.db.models.price_history import PriceHistory
from app.db.models.product_match import ProductMatch
from app.db.models.user import User
from app.db.models.alert import PriceAlert, SearchHistory

__all__ = [
    "Marketplace",
    "Category",
    "Product",
    "PriceHistory",
    "ProductMatch",
    "User",
    "PriceAlert",
    "SearchHistory",
]
'@
Set-Content -Path "backend/app/db/models/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/db/models/__init__.py" -ForegroundColor Green

# backend/app/schemas/__init__.py
$content = @'
"""Pydantic schemas."""

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
)
from app.schemas.search import (
    SearchQuery,
    SearchResponse,
)
'@
Set-Content -Path "backend/app/schemas/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/schemas/__init__.py" -ForegroundColor Green

# backend/app/services/__init__.py
$content = @'
"""Business logic services."""

from app.services.product_service import ProductService
from app.services.search_service import SearchService
'@
Set-Content -Path "backend/app/services/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/services/__init__.py" -ForegroundColor Green

# backend/app/scrapers/__init__.py
$content = @'
"""Marketplace scrapers."""
'@
Set-Content -Path "backend/app/scrapers/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/scrapers/__init__.py" -ForegroundColor Green

# backend/app/ml/__init__.py
$content = @'
"""Machine learning components."""
'@
Set-Content -Path "backend/app/ml/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/ml/__init__.py" -ForegroundColor Green

# backend/app/agents/__init__.py
$content = @'
"""AI agents."""
'@
Set-Content -Path "backend/app/agents/__init__.py" -Value $content -Force
Write-Host "  Created: backend/app/agents/__init__.py" -ForegroundColor Green

# backend/tests/__init__.py
$content = @'
"""Tests package."""
'@
Set-Content -Path "backend/tests/__init__.py" -Value $content -Force
Write-Host "  Created: backend/tests/__init__.py" -ForegroundColor Green

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Cyan
Write-Host "All __init__.py files created with proper exports." -ForegroundColor Green
