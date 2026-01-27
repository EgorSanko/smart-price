"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, products, search

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(products.router)
api_router.include_router(search.router)

# Future routers will be added here:
# api_router.include_router(analytics.router)
# api_router.include_router(chat.router)
# api_router.include_router(users.router)
# api_router.include_router(alerts.router)
