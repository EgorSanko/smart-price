"""Base scraper classes for marketplace parsing.

This module provides abstract base classes for building marketplace scrapers
with built-in rate limiting, retry logic, and browser automation support.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncGenerator

import httpx
from playwright.async_api import Browser, Page, async_playwright
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    from app.schemas.product import ProductCreate

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


class RateLimitError(ScraperError):
    """Raised when rate limit is exceeded."""

    pass


class BlockedError(ScraperError):
    """Raised when scraper is blocked by the website."""

    pass


class BaseScraper(ABC):
    """Abstract base class for all marketplace scrapers.

    Provides common functionality including:
    - HTTP client with custom headers
    - Rate limiting
    - Retry logic with exponential backoff
    - Graceful resource cleanup

    Attributes:
        marketplace_name: Unique identifier for the marketplace.
        base_url: Base URL of the marketplace.
        rate_limit: Maximum requests per second.
    """

    marketplace_name: str
    base_url: str
    rate_limit: float = 1.0

    def __init__(self, proxy_url: str | None = None) -> None:
        """Initialize the scraper.

        Args:
            proxy_url: Optional proxy URL for requests.
        """
        self._proxy_url = proxy_url
        self._last_request_time: float = 0.0
        self._client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get default HTTP headers for requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Configured async HTTP client.
        """
        if self._client is None:
            transport = None
            if self._proxy_url:
                transport = httpx.AsyncHTTPTransport(proxy=self._proxy_url)

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers=self._get_headers(),
                follow_redirects=True,
                transport=transport,
            )
        return self._client

    async def _rate_limit_wait(self) -> None:
        """Wait to respect rate limiting."""
        if self.rate_limit <= 0:
            return

        elapsed = time.monotonic() - self._last_request_time
        min_interval = 1.0 / self.rate_limit

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self._last_request_time = time.monotonic()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def fetch(self, url: str) -> str:
        """Fetch HTML content from URL with retry logic.

        Args:
            url: URL to fetch.

        Returns:
            HTML content as string.

        Raises:
            httpx.HTTPStatusError: If response status is 4xx/5xx.
            RateLimitError: If rate limited (429).
            BlockedError: If access is blocked (403).
        """
        await self._rate_limit_wait()

        client = await self._get_client()

        logger.debug("Fetching URL: %s", url)
        response = await client.get(url)

        if response.status_code == 429:
            raise RateLimitError(f"Rate limited on {url}")

        if response.status_code == 403:
            raise BlockedError(f"Blocked on {url}")

        response.raise_for_status()
        return response.text

    async def fetch_json(self, url: str, params: dict | None = None) -> dict:
        """Fetch JSON data from URL.

        Args:
            url: URL to fetch.
            params: Optional query parameters.

        Returns:
            Parsed JSON as dictionary.
        """
        await self._rate_limit_wait()

        client = await self._get_client()

        logger.debug("Fetching JSON: %s", url)
        response = await client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    @abstractmethod
    async def search(
        self,
        query: str,
        page: int = 1,
        **kwargs,
    ) -> list[ProductCreate]:
        """Search for products.

        Args:
            query: Search query string.
            page: Page number (1-indexed).
            **kwargs: Additional search parameters.

        Returns:
            List of found products.
        """
        pass

    @abstractmethod
    async def get_product(self, product_id: str) -> ProductCreate | None:
        """Get single product by ID.

        Args:
            product_id: Marketplace-specific product ID.

        Returns:
            Product data or None if not found.
        """
        pass

    @abstractmethod
    async def get_category(
        self,
        category_url: str,
        max_pages: int = 10,
    ) -> AsyncGenerator[ProductCreate, None]:
        """Iterate over all products in a category.

        Args:
            category_url: URL of the category page.
            max_pages: Maximum number of pages to scrape.

        Yields:
            Product data for each product in the category.
        """
        pass

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseScraper":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


class PlaywrightScraper(BaseScraper):
    """Base scraper using Playwright for JavaScript-heavy websites.

    Extends BaseScraper with browser automation capabilities for sites
    that require JavaScript execution to render content.
    """

    def __init__(
        self,
        proxy_url: str | None = None,
        headless: bool = True,
    ) -> None:
        """Initialize Playwright scraper.

        Args:
            proxy_url: Optional proxy URL.
            headless: Run browser in headless mode.
        """
        super().__init__(proxy_url)
        self._headless = headless
        self._playwright = None
        self._browser: Browser | None = None

    async def _get_browser(self) -> Browser:
        """Get or create browser instance.

        Returns:
            Playwright browser instance.
        """
        if self._browser is None:
            self._playwright = await async_playwright().start()

            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
            ]

            proxy_config = None
            if self._proxy_url:
                proxy_config = {"server": self._proxy_url}

            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
                args=launch_args,
                proxy=proxy_config,
            )

        return self._browser

    async def _create_page(self) -> Page:
        """Create new browser page with stealth settings.

        Returns:
            Configured browser page.
        """
        browser = await self._get_browser()

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self._get_headers()["User-Agent"],
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            permissions=["geolocation"],
            geolocation={"latitude": 55.7558, "longitude": 37.6173},
        )

        # Block unnecessary resources to speed up loading
        page = await context.new_page()
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}",
            lambda route: route.abort(),
        )

        # Inject stealth scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        return page

    async def fetch_js(
        self,
        url: str,
        wait_selector: str | None = None,
        wait_timeout: int = 10000,
    ) -> str:
        """Fetch page content after JavaScript execution.

        Args:
            url: URL to fetch.
            wait_selector: CSS selector to wait for before returning.
            wait_timeout: Maximum time to wait for selector (ms).

        Returns:
            Rendered HTML content.
        """
        await self._rate_limit_wait()

        page = await self._create_page()
        try:
            logger.debug("Fetching with JS: %s", url)
            await page.goto(url, wait_until="networkidle")

            if wait_selector:
                await page.wait_for_selector(
                    wait_selector,
                    timeout=wait_timeout,
                )

            return await page.content()
        finally:
            await page.close()

    async def scroll_and_load(
        self,
        url: str,
        scroll_count: int = 5,
        scroll_delay: float = 1.0,
    ) -> str:
        """Fetch page with infinite scroll handling.

        Args:
            url: URL to fetch.
            scroll_count: Number of scroll iterations.
            scroll_delay: Delay between scrolls (seconds).

        Returns:
            Rendered HTML content after scrolling.
        """
        await self._rate_limit_wait()

        page = await self._create_page()
        try:
            await page.goto(url, wait_until="networkidle")

            for _ in range(scroll_count):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(scroll_delay)
                await page.wait_for_load_state("networkidle")

            return await page.content()
        finally:
            await page.close()

    async def close(self) -> None:
        """Close browser and HTTP client."""
        await super().close()

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
