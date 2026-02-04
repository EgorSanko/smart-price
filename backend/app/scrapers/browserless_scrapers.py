"""Wildberries scraper with browserless support.

Uses Playwright connected to browserless container for anti-detection.
Based on working solutions from GitHub community.

Key features:
- Connects to browserless via WebSocket (stealth mode enabled)
- Falls back to httpx if browserless unavailable
- Uses catalog.wb.ru API (less blocking than search.wb.ru)
- Proper rate limiting and retry logic
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import TYPE_CHECKING, Any, AsyncGenerator

import httpx

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page
    from app.schemas.product import ProductCreate

logger = logging.getLogger(__name__)


class WildberriesScraper:
    """Wildberries marketplace scraper with browserless support.

    Connects to browserless container via Playwright WebSocket for
    stealth browsing that bypasses anti-bot detection.

    Environment variables:
        PLAYWRIGHT_WS_ENDPOINT: WebSocket URL (e.g., ws://browserless:3000)
        USE_BROWSERLESS: Set to 'true' to enable browserless

    Example:
        >>> scraper = WildberriesScraper()
        >>> products = await scraper.search("iphone 15")
        >>> print(f"Found {len(products)} products")
    """

    marketplace_name: str = "wildberries"
    base_url: str = "https://www.wildberries.ru"

    # API endpoints
    SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v9/search"
    CATALOG_URL = "https://catalog.wb.ru/catalog/{shard}/catalog"
    CARD_URL = "https://card.wb.ru/cards/v2/detail"
    MENU_URL = "https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json"

    # Default destination (Moscow region)
    DEFAULT_DEST = -1257786

    def __init__(
        self,
        marketplace_id: int = 2,
        use_browserless: bool | None = None,
        ws_endpoint: str | None = None,
    ) -> None:
        """Initialize scraper.

        Args:
            marketplace_id: ID in database (default 2 for WB).
            use_browserless: Force browserless on/off. If None, reads from env.
            ws_endpoint: Playwright WebSocket endpoint. If None, reads from env.
        """
        self._marketplace_id = marketplace_id
        self._dest = self.DEFAULT_DEST

        # Browserless config
        if use_browserless is None:
            use_browserless = os.getenv("USE_BROWSERLESS", "").lower() == "true"
        self._use_browserless = use_browserless

        if ws_endpoint is None:
            ws_endpoint = os.getenv("PLAYWRIGHT_WS_ENDPOINT", "ws://browserless:3000")
        self._ws_endpoint = ws_endpoint

        # Browser state
        self._browser: Browser | None = None
        self._playwright = None

    def _get_headers(self) -> dict[str, str]:
        """Get realistic browser headers."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://www.wildberries.ru",
            "Referer": "https://www.wildberries.ru/",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }

    # =========================================================================
    # BROWSERLESS / PLAYWRIGHT METHODS
    # =========================================================================

    async def _get_browser(self) -> Browser:
        """Connect to browserless via WebSocket."""
        if self._browser and self._browser.is_connected():
            return self._browser

        try:
            from playwright.async_api import async_playwright

            logger.info(f"Connecting to browserless: {self._ws_endpoint}")

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.connect_over_cdp(
                self._ws_endpoint
            )

            logger.info("Connected to browserless successfully")
            return self._browser

        except Exception as e:
            logger.error(f"Failed to connect to browserless: {e}")
            raise

    async def _get_page(self) -> Page:
        """Get new browser page with stealth settings."""
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self._get_headers()["User-Agent"],
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            # Extra stealth
            java_script_enabled=True,
            bypass_csp=True,
        )

        page = await context.new_page()

        # Block unnecessary resources for speed
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,mp4,webm}",
            lambda route: route.abort(),
        )

        return page

    async def _fetch_with_browser(self, url: str) -> dict | None:
        """Fetch JSON data using browserless."""
        page = None
        try:
            page = await self._get_page()

            # Navigate and wait
            logger.debug(f"Fetching with browser: {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            if response and response.status == 200:
                content = await page.content()
                # Extract JSON from page
                import json
                import re

                # Try to find JSON in page
                json_match = re.search(r"<pre[^>]*>(.*?)</pre>", content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

                # Or page might be raw JSON
                try:
                    body = await page.inner_text("body")
                    return json.loads(body)
                except Exception:
                    pass

            logger.warning(f"Browser fetch failed: status={response.status if response else 'None'}")
            return None

        except Exception as e:
            logger.error(f"Browser fetch error: {e}")
            return None

        finally:
            if page:
                await page.close()

    # =========================================================================
    # HTTP METHODS (fallback)
    # =========================================================================

    async def _fetch_with_httpx(
        self,
        url: str,
        params: dict | None = None,
        retries: int = 3,
    ) -> dict | None:
        """Fetch JSON data using httpx (fallback method)."""
        for attempt in range(retries):
            try:
                # Random delay
                await asyncio.sleep(random.uniform(1.5, 4.0))

                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0),
                    headers=self._get_headers(),
                    follow_redirects=True,
                ) as client:
                    response = await client.get(url, params=params)

                    if response.status_code == 429:
                        wait = (attempt + 1) * 15
                        logger.warning(f"Rate limited (429), waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue

                    if response.status_code in (403, 498):
                        logger.warning(f"Blocked ({response.status_code})")
                        return None

                    response.raise_for_status()
                    return response.json()

            except Exception as e:
                logger.warning(f"HTTP request error (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)

        return None

    async def _fetch(self, url: str, params: dict | None = None) -> dict | None:
        """Fetch data using best available method."""
        # Build full URL with params
        if params:
            from urllib.parse import urlencode
            full_url = f"{url}?{urlencode(params)}"
        else:
            full_url = url

        # Try browserless first if enabled
        if self._use_browserless:
            try:
                result = await self._fetch_with_browser(full_url)
                if result:
                    return result
                logger.warning("Browserless failed, falling back to httpx")
            except Exception as e:
                logger.warning(f"Browserless error: {e}, falling back to httpx")

        # Fallback to httpx
        return await self._fetch_with_httpx(url, params)

    # =========================================================================
    # PARSING METHODS
    # =========================================================================

    @staticmethod
    def _get_basket_host(vol: int) -> str:
        """Get CDN basket host for product images."""
        ranges = [
            (143, "01"), (287, "02"), (431, "03"), (719, "04"),
            (1007, "05"), (1061, "06"), (1115, "07"), (1169, "08"),
            (1313, "09"), (1601, "10"), (1655, "11"), (1919, "12"),
            (2045, "13"), (2189, "14"), (2405, "15"), (2621, "16"),
        ]
        for limit, basket in ranges:
            if vol <= limit:
                return basket
        return "17"

    def _build_image_url(self, product_id: int, num: int = 1) -> str:
        """Build image URL for product."""
        vol = product_id // 100000
        part = product_id // 1000
        basket = self._get_basket_host(vol)
        return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/{num}.webp"

    def _parse_product(self, item: dict) -> dict[str, Any]:
        """Parse product from API response."""
        product_id = item.get("id", 0)

        # Price handling (WB stores in kopecks)
        sizes = item.get("sizes", [])
        if sizes:
            price_data = sizes[0].get("price", {})
            price = price_data.get("product", 0) / 100
            original = price_data.get("basic", 0) / 100
        else:
            price = item.get("salePriceU", 0) / 100
            original = item.get("priceU", 0) / 100

        # Availability
        is_available = any(s.get("stocks") for s in sizes) if sizes else True

        return {
            "external_id": str(product_id),
            "title": item.get("name", ""),
            "brand": item.get("brand", ""),
            "price": price,
            "original_price": original if original > price else None,
            "url": f"{self.base_url}/catalog/{product_id}/detail.aspx",
            "image_url": self._build_image_url(product_id),
            "images": [self._build_image_url(product_id, i) for i in range(1, 4)],
            "rating": item.get("reviewRating") or item.get("rating"),
            "reviews_count": item.get("feedbacks", 0),
            "is_available": is_available,
            "seller_name": item.get("supplier"),
        }

    def _to_product_create(self, data: dict) -> ProductCreate:
        """Convert parsed data to ProductCreate schema."""
        from app.schemas.product import ProductCreate

        return ProductCreate(
            external_id=data["external_id"],
            marketplace_id=self._marketplace_id,
            title=data["title"],
            brand=data.get("brand"),
            current_price=data["price"],
            original_price=data.get("original_price"),
            url=data["url"],
            image_url=data.get("image_url"),
            images=data.get("images", []),
            rating=data.get("rating"),
            reviews_count=data.get("reviews_count", 0),
            is_available=data.get("is_available", True),
            seller_name=data.get("seller_name"),
        )

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 100,
    ) -> list[ProductCreate]:
        """Search products by query.

        Args:
            query: Search query string.
            page: Page number (1-based).
            limit: Max results per page.

        Returns:
            List of ProductCreate objects.
        """
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": str(self._dest),
            "page": str(page),
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "spp": "30",
            "suppressSpellcheck": "false",
        }

        logger.info(f"Searching WB: '{query}' page={page}")

        data = await self._fetch(self.SEARCH_URL, params)
        if not data:
            logger.warning("Search returned no data")
            return []

        products = []
        items = data.get("data", {}).get("products", [])

        for item in items[:limit]:
            try:
                parsed = self._parse_product(item)
                if parsed["price"] > 0:
                    products.append(self._to_product_create(parsed))
            except Exception as e:
                logger.warning(f"Parse error: {e}")

        logger.info(f"Found {len(products)} products for '{query}'")
        return products

    async def get_product(self, product_id: str) -> ProductCreate | None:
        """Get single product by ID.

        Args:
            product_id: Wildberries product ID (nm).

        Returns:
            ProductCreate or None if not found.
        """
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": str(self._dest),
            "nm": product_id,
        }

        logger.info(f"Getting WB product: {product_id}")

        data = await self._fetch(self.CARD_URL, params)
        if not data:
            return None

        items = data.get("data", {}).get("products", [])
        if not items:
            return None

        parsed = self._parse_product(items[0])
        return self._to_product_create(parsed)

    async def get_category(
        self,
        shard: str,
        max_pages: int = 5,
    ) -> AsyncGenerator[ProductCreate, None]:
        """Iterate products in category.

        Args:
            shard: Category shard (e.g., 'electronic', 'clothes').
            max_pages: Maximum pages to fetch.

        Yields:
            ProductCreate objects.
        """
        url = self.CATALOG_URL.format(shard=shard)

        for page in range(1, max_pages + 1):
            params = {
                "appType": "1",
                "curr": "rub",
                "dest": str(self._dest),
                "page": str(page),
                "sort": "popular",
                "spp": "30",
            }

            logger.info(f"Fetching category: shard={shard} page={page}")

            data = await self._fetch(url, params)
            if not data:
                break

            items = data.get("data", {}).get("products", [])
            if not items:
                break

            for item in items:
                try:
                    parsed = self._parse_product(item)
                    if parsed["price"] > 0:
                        yield self._to_product_create(parsed)
                except Exception as e:
                    logger.warning(f"Parse error: {e}")

            # Delay between pages
            await asyncio.sleep(random.uniform(2, 5))

    async def close(self) -> None:
        """Close browser connection."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# =============================================================================
# OZON SCRAPER (similar structure)
# =============================================================================

class OzonScraper:
    """Ozon marketplace scraper with browserless support.

    Similar to WildberriesScraper but for Ozon.
    Ozon has more aggressive anti-bot, so browserless is recommended.
    """

    marketplace_name: str = "ozon"
    base_url: str = "https://www.ozon.ru"

    def __init__(
        self,
        marketplace_id: int = 1,
        use_browserless: bool | None = None,
        ws_endpoint: str | None = None,
    ) -> None:
        """Initialize Ozon scraper."""
        self._marketplace_id = marketplace_id

        if use_browserless is None:
            use_browserless = os.getenv("USE_BROWSERLESS", "").lower() == "true"
        self._use_browserless = use_browserless

        if ws_endpoint is None:
            ws_endpoint = os.getenv("PLAYWRIGHT_WS_ENDPOINT", "ws://browserless:3000")
        self._ws_endpoint = ws_endpoint

        self._browser: Browser | None = None
        self._playwright = None

    async def _get_browser(self) -> Browser:
        """Connect to browserless."""
        if self._browser and self._browser.is_connected():
            return self._browser

        from playwright.async_api import async_playwright

        logger.info(f"Connecting to browserless for Ozon: {self._ws_endpoint}")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(
            self._ws_endpoint
        )
        return self._browser

    async def _get_page(self) -> Page:
        """Get browser page."""
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )
        page = await context.new_page()

        # Block heavy resources
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,mp4,webm}",
            lambda route: route.abort(),
        )

        return page

    async def search(
        self,
        query: str,
        page: int = 1,
    ) -> list[ProductCreate]:
        """Search products on Ozon.

        Ozon requires browser-based scraping due to heavy JS.
        """
        if not self._use_browserless:
            logger.warning("Ozon requires browserless for scraping")
            return []

        browser_page = None
        try:
            browser_page = await self._get_page()

            url = f"{self.base_url}/search/?text={query}&page={page}"
            logger.info(f"Searching Ozon: '{query}' page={page}")

            await browser_page.goto(url, wait_until="networkidle", timeout=60000)

            # Wait for products to load
            await browser_page.wait_for_selector('[data-widget="searchResultsV2"]', timeout=10000)

            # Extract product data from page
            products = await browser_page.evaluate("""
                () => {
                    const items = [];
                    document.querySelectorAll('[data-widget="searchResultsV2"] > div > div').forEach(el => {
                        const link = el.querySelector('a[href*="/product/"]');
                        const priceEl = el.querySelector('[data-widget="searchResultsV2"] span[style*="font-weight"]');

                        if (link) {
                            items.push({
                                url: link.href,
                                title: link.textContent?.trim() || '',
                            });
                        }
                    });
                    return items;
                }
            """)

            logger.info(f"Found {len(products)} products on Ozon")

            # Convert to ProductCreate (simplified)
            from app.schemas.product import ProductCreate

            result = []
            for item in products[:50]:
                # Extract ID from URL
                import re
                match = re.search(r"/product/[^/]+-(\d+)", item.get("url", ""))
                if match:
                    result.append(ProductCreate(
                        external_id=match.group(1),
                        marketplace_id=self._marketplace_id,
                        title=item.get("title", "Unknown"),
                        current_price=0,  # Would need more parsing
                        url=item.get("url", ""),
                    ))

            return result

        except Exception as e:
            logger.error(f"Ozon search error: {e}")
            return []

        finally:
            if browser_page:
                await browser_page.close()

    async def close(self) -> None:
        """Close browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_scraper(
    marketplace: str,
    use_browserless: bool | None = None,
) -> WildberriesScraper | OzonScraper:
    """Get scraper instance by marketplace name.

    Args:
        marketplace: 'wildberries' or 'ozon'.
        use_browserless: Override browserless setting.

    Returns:
        Scraper instance.

    Example:
        >>> scraper = get_scraper("wildberries")
        >>> products = await scraper.search("iphone")
    """
    scrapers = {
        "wildberries": WildberriesScraper,
        "wb": WildberriesScraper,
        "ozon": OzonScraper,
    }

    scraper_class = scrapers.get(marketplace.lower())
    if not scraper_class:
        raise ValueError(f"Unknown marketplace: {marketplace}")

    return scraper_class(use_browserless=use_browserless)
