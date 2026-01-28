"""Marketplace scrapers module.

This module provides scrapers for various Russian e-commerce marketplaces.
Each scraper implements the BaseScraper interface for consistent usage.

Available scrapers:
    - OzonScraper: Scraper for ozon.ru (requires Playwright)
    - WildberriesScraper: Scraper for wildberries.ru (uses public API)

Example:
    >>> from app.scrapers import get_scraper
    >>>
    >>> async with get_scraper("wildberries") as scraper:
    ...     products = await scraper.search("iphone 15")
    ...     for p in products:
    ...         print(f"{p.title}: {p.current_price} ₽")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.scrapers.base import (
    BaseScraper,
    BlockedError,
    PlaywrightScraper,
    RateLimitError,
    ScraperError,
)
from app.scrapers.ozon import OzonScraper
from app.scrapers.utils import (
    ProxyRotator,
    RateLimiter,
    clean_text,
    extract_product_id,
    get_random_headers,
    get_random_user_agent,
    human_like_delay,
    parse_price,
    random_delay,
    with_retry,
)
from app.scrapers.wildberries import WildberriesScraper

if TYPE_CHECKING:
    pass

__all__ = [
    # Base classes
    "BaseScraper",
    "PlaywrightScraper",
    # Exceptions
    "ScraperError",
    "RateLimitError",
    "BlockedError",
    # Scrapers
    "OzonScraper",
    "WildberriesScraper",
    # Factory
    "get_scraper",
    "SCRAPER_REGISTRY",
    # Utilities
    "get_random_user_agent",
    "get_random_headers",
    "random_delay",
    "human_like_delay",
    "RateLimiter",
    "with_retry",
    "parse_price",
    "clean_text",
    "extract_product_id",
    "ProxyRotator",
]

# Registry of available scrapers
SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "ozon": OzonScraper,
    "wildberries": WildberriesScraper,
    "wb": WildberriesScraper,  # Alias
}


def get_scraper(
    marketplace: str,
    marketplace_id: int | None = None,
    proxy_url: str | None = None,
    **kwargs,
) -> BaseScraper:
    """Factory function to get scraper instance by marketplace name.

    Args:
        marketplace: Marketplace name ('ozon', 'wildberries', 'wb').
        marketplace_id: Optional database ID for the marketplace.
        proxy_url: Optional proxy URL for requests.
        **kwargs: Additional arguments passed to scraper constructor.

    Returns:
        Scraper instance for the specified marketplace.

    Raises:
        ValueError: If marketplace is not supported.

    Example:
        >>> scraper = get_scraper("ozon", proxy_url="http://proxy:8080")
        >>> try:
        ...     products = await scraper.search("laptop")
        ... finally:
        ...     await scraper.close()
    """
    marketplace_lower = marketplace.lower().strip()

    if marketplace_lower not in SCRAPER_REGISTRY:
        supported = ", ".join(sorted(set(SCRAPER_REGISTRY.keys()) - {"wb"}))
        raise ValueError(
            f"Unsupported marketplace: '{marketplace}'. "
            f"Supported: {supported}"
        )

    scraper_class = SCRAPER_REGISTRY[marketplace_lower]

    # Determine default marketplace_id if not provided
    if marketplace_id is None:
        marketplace_id = {
            "ozon": 1,
            "wildberries": 2,
            "wb": 2,
        }.get(marketplace_lower, 0)

    return scraper_class(
        marketplace_id=marketplace_id,
        proxy_url=proxy_url,
        **kwargs,
    )


async def search_all_marketplaces(
    query: str,
    marketplaces: list[str] | None = None,
    proxy_url: str | None = None,
) -> dict[str, list]:
    """Search across multiple marketplaces simultaneously.

    Args:
        query: Search query string.
        marketplaces: List of marketplace names. If None, search all.
        proxy_url: Optional proxy URL.

    Returns:
        Dictionary mapping marketplace names to product lists.

    Example:
        >>> results = await search_all_marketplaces("iphone 15")
        >>> for marketplace, products in results.items():
        ...     print(f"{marketplace}: {len(products)} products")
    """
    import asyncio

    if marketplaces is None:
        marketplaces = ["ozon", "wildberries"]

    async def search_marketplace(name: str) -> tuple[str, list]:
        try:
            async with get_scraper(name, proxy_url=proxy_url) as scraper:
                products = await scraper.search(query)
                return name, products
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "Failed to search %s: %s", name, e
            )
            return name, []

    tasks = [search_marketplace(name) for name in marketplaces]
    results = await asyncio.gather(*tasks)

    return dict(results)
