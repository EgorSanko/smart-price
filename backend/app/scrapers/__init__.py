"""Marketplace scraper registry.

Provides factory function for getting scraper instances by name.
All heavy imports (scrapling, playwright) are lazy to avoid startup crashes.

Usage:
    from app.scrapers import get_scraper, list_scrapers

    scraper = get_scraper("onliner")
    products = await scraper.search("iPhone 15")
"""

__all__ = [
    "get_scraper",
    "list_scrapers",
]

_SUPPORTED = ["onliner", "ozon", "wildberries", "yandex"]


def get_scraper(marketplace: str):
    """Create a scraper instance for the given marketplace.

    Args:
        marketplace: Marketplace name (e.g. "onliner", "wildberries").

    Returns:
        Configured scraper instance.

    Raises:
        ValueError: If marketplace is not supported.
    """
    name = marketplace.lower()
    if name == "onliner":
        from app.scrapers.onliner import OnlinerScraper

        return OnlinerScraper()
    if name == "wildberries":
        from app.scrapers.wildberries import WildberriesScraper

        return WildberriesScraper()
    if name == "ozon":
        from app.scrapers.ozon import OzonScraper

        return OzonScraper()
    if name == "yandex":
        from app.scrapers.yandex_market import YandexMarketScraper

        return YandexMarketScraper()

    supported = ", ".join(sorted(_SUPPORTED))
    raise ValueError(f"Unknown marketplace '{marketplace}'. Supported: {supported}")


def list_scrapers() -> list[str]:
    """List all supported marketplace names."""
    return sorted(_SUPPORTED)
