"""Price history endpoint - fetches data from Onliner API."""

from fastapi import APIRouter, Query

from app.scrapers.onliner import OnlinerScraper


router = APIRouter(prefix="/products", tags=["products"])


@router.get("/history")
async def get_price_history(
    product_key: str = Query(..., min_length=1, description="Onliner product key"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
) -> dict:
    """Get price history for an Onliner product."""
    scraper = OnlinerScraper()
    result = await scraper.get_price_history(product_key)
    result["days"] = days
    return result
