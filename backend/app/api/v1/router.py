"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analyze,
    auth,
    catalog,
    chat,
    cheaper,
    compare,
    health,
    image_proxy,
    onliner_product,
    parsers,
    payments,
    price_history,
    products,
    search,
    search_stream,
)


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(payments.router)
api_router.include_router(health.router)
api_router.include_router(price_history.router)  # Before products (has /{product_id} catch-all)
api_router.include_router(products.router)
api_router.include_router(search.router)
api_router.include_router(search_stream.router)
api_router.include_router(chat.router)
api_router.include_router(compare.router)
api_router.include_router(parsers.router)
api_router.include_router(image_proxy.router)
api_router.include_router(catalog.router)
api_router.include_router(onliner_product.router)
api_router.include_router(analyze.router)
api_router.include_router(cheaper.router)

# Future routers will be added here:
# api_router.include_router(analytics.router)
# api_router.include_router(users.router)
# api_router.include_router(alerts.router)
