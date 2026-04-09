"""Scraping manager — orchestrates all marketplace parsers."""

import asyncio

import structlog


logger = structlog.get_logger()

# Registry of parsers
_parsers: dict = {}


def get_parsers(region: str = "all") -> dict:
    """Get parsers filtered by region."""
    if not _parsers:
        _register_default_parsers()
    if region == "all":
        return _parsers
    return {k: v for k, v in _parsers.items() if v.get("region") == region or region == "all"}


def _register_default_parsers():
    """Register all available parsers."""
    global _parsers
    _parsers = {
        "onliner": {
            "name": "Onliner BY",
            "region": "BY",
            "color": "#65cb02",
            "enabled": True,
        },
        "yandex": {
            "name": "Яндекс Маркет",
            "region": "RU",
            "color": "#ffcc00",
            "enabled": True,
        },
        "wildberries": {
            "name": "Wildberries",
            "region": "RU",
            "color": "#cb11ab",
            # Disabled: search API returns OOS items with prices,
            # and stock fields (totalQuantity, sizes.stocks) are unreliable/stale.
            # Also returns refurbished items mixed with new ones.
            "enabled": False,
        },
        "citilink": {
            "name": "Ситилинк",
            "region": "RU",
            "color": "#ff6600",
            # Disabled: price extraction returns unreliable values
            # (club/card prices vs real prices). Re-enable after parser fix.
            "enabled": False,
        },
        "regard": {
            "name": "Регард",
            "region": "RU",
            "color": "#e53935",
            "enabled": True,
        },
        "aliexpress": {
            "name": "AliExpress",
            "region": "RU",
            "color": "#ff4747",
            "enabled": False,
        },
        "worlddevices": {
            "name": "World Devices",
            "region": "RU",
            "color": "#2196f3",
            "enabled": True,
        },
        "oneclick": {
            "name": "1click",
            "region": "RU",
            "color": "#0084ff",
            "enabled": True,
        },
        "biggeek": {
            "name": "BigGeek",
            "region": "RU",
            "color": "#7b1fa2",
            "enabled": True,
        },
    }


async def search_all(
    query: str,
    region: str = "all",
    max_price: float | None = None,
) -> list[dict]:
    """Search across all enabled parsers. Returns flat list of products."""
    from app.scrapers.ai_relevance_filter import ai_filter_relevant

    manager = ScrapingManager()
    results = await manager.search_all(query, region)

    all_products = []
    for products in results.values():
        all_products.extend(products)

    # AI-powered relevance filter
    all_products = await ai_filter_relevant(all_products, query)

    all_products.sort(key=lambda x: x.get("price_num", 0))

    if max_price:
        all_products = [p for p in all_products if p.get("price_num", 0) <= max_price]

    return all_products


class ScrapingManager:
    """Central manager for all scraping operations."""

    def __init__(self) -> None:
        self.logger = structlog.get_logger()

    async def search_all(
        self,
        query: str,
        region: str = "all",
    ) -> dict[str, list[dict]]:
        """Search across all marketplaces in parallel."""
        tasks: dict[str, asyncio.Task] = {}

        parsers = get_parsers(region)

        for key, info in parsers.items():
            if not info.get("enabled"):
                continue
            tasks[key] = asyncio.create_task(self._safe_search(key, query))

        results: dict[str, list[dict]] = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                self.logger.error("search_failed", marketplace=key, error=str(e))
                results[key] = []

        return results

    async def _safe_search(self, marketplace: str, query: str) -> list[dict]:
        """Search a single marketplace with error handling."""
        try:
            if marketplace == "onliner":
                from app.scrapers.onliner import OnlinerScraper

                scraper = OnlinerScraper()
                return await scraper.search(query)
            elif marketplace == "yandex":
                from app.scrapers.playwright_scrapers import YandexMarketPlaywright

                scraper = YandexMarketPlaywright()
                return await scraper.search(query)
            elif marketplace == "wildberries":
                from app.scrapers.playwright_scrapers import WildberriesPlaywright

                scraper = WildberriesPlaywright()
                return await scraper.search(query)
            elif marketplace == "citilink":
                from app.scrapers.playwright_scrapers import CitilinkPlaywright

                scraper = CitilinkPlaywright()
                return await scraper.search(query)
            elif marketplace == "regard":
                from app.scrapers.regard_http import RegardHttpScraper

                scraper = RegardHttpScraper()
                return await scraper.search(query)
            elif marketplace == "aliexpress":
                from app.scrapers.playwright_scrapers import AliExpressPlaywright

                scraper = AliExpressPlaywright()
                return await scraper.search(query)
            elif marketplace == "worlddevices":
                from app.scrapers.worlddevices_http import WorldDevicesHttpScraper

                scraper = WorldDevicesHttpScraper()
                return await scraper.search(query)
            elif marketplace == "oneclick":
                from app.scrapers.oneclick_http import OneclickHttpScraper

                scraper = OneclickHttpScraper()
                return await scraper.search(query)
            elif marketplace == "biggeek":
                from app.scrapers.biggeek_http import BigGeekHttpScraper

                scraper = BigGeekHttpScraper()
                return await scraper.search(query)
            else:
                self.logger.warning("unknown_marketplace", marketplace=marketplace)
                return []
        except Exception as e:
            self.logger.error("scraper_error", marketplace=marketplace, error=str(e))
            return []
