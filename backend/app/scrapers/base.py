"""Base scraper framework built on Scrapling + anti-detection layer.

Why existing tools alone don't work against Ozon/WB:
- StealthyFetcher solves TLS/fingerprint detection, but marketplaces
  also detect by **behavior**: fixed timing, no scrolling, no session history.
- Residential proxies solve IP reputation, but without behavior simulation
  the proxy just gets burned faster.

This module combines Scrapling's stealth capabilities with:
1. ProxyRotator — health-tracked residential proxy pool
2. HumanBehavior — variable delays, scroll simulation, page_action callbacks
3. SessionManager — maintains browsing context (cookies, history, warmup)
4. Response analysis — detects captchas, blocks, empty pages
5. Adaptive rate limiting — backs off on detection, recovers on success
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from scrapling.fetchers import (
    AsyncFetcher,
    AsyncStealthySession,
    Fetcher,
    StealthyFetcher,
)

from app.scrapers.antidetect import (
    HumanBehavior,
    ProxyRotator,
    ScrapingSession,
    SessionManager,
    build_antidetect_config,
)


if TYPE_CHECKING:
    from scrapling.parser import Selector

    from app.schemas.product import ProductCreate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Adaptive parsing — survive DOM changes between runs
# ---------------------------------------------------------------------------
Fetcher.adaptive = True
StealthyFetcher.adaptive = True


# ---------------------------------------------------------------------------
# Shared proxy pool (singleton, loaded once from settings)
# ---------------------------------------------------------------------------
_proxy_rotator: ProxyRotator | None = None


def _get_proxy_rotator() -> ProxyRotator:
    """Lazy-init shared proxy rotator from settings."""
    global _proxy_rotator
    if _proxy_rotator is None:
        _proxy_rotator = ProxyRotator.from_settings()
    return _proxy_rotator


# ---------------------------------------------------------------------------
# Response analysis (ban/block detection)
# ---------------------------------------------------------------------------

_CAPTCHA_MARKERS = [
    "captcha",
    "recaptcha",
    "hcaptcha",
    "turnstile",
    "verify you are human",
    "challenge-platform",
    "подтвердите, что вы не робот",
    "проверка безопасности",
]

_BLOCK_MARKERS = [
    "access denied",
    "доступ ограничен",
    "подозрительная активность",
    "automated",
    "bot detection",
    "too many requests",
]

_CF_MARKERS = [
    "cf-browser-verification",
    "checking your browser",
    "just a moment",
    "ray id",
]


def _is_blocked(status: int, body: str) -> str | None:
    """Check if response indicates a block.

    Args:
        status: HTTP response status code.
        body: Response body text.

    Returns:
        Block reason string, or None if not blocked.
    """
    if status == 403:
        return "http_403"
    if status == 429:
        return "rate_limited"
    if status in (503, 520, 521, 522, 523):
        return f"http_{status}"

    body_lower = body[:3000].lower()

    for marker in _CAPTCHA_MARKERS:
        if marker in body_lower:
            return "captcha"

    for marker in _CF_MARKERS:
        if marker in body_lower:
            return "cloudflare"

    for marker in _BLOCK_MARKERS:
        if marker in body_lower:
            return "blocked"

    # Suspiciously short response for a real product page
    if status == 200 and len(body) < 500:
        return "empty_response"

    return None


# ---------------------------------------------------------------------------
# BaseScraper
# ---------------------------------------------------------------------------


class BaseScraper(ABC):
    """Abstract base for all marketplace scrapers.

    Provides:
    - Adaptive rate limiting (slows down on blocks, recovers on success)
    - Proxy integration via shared ProxyRotator
    - Session management for consistent browsing identity
    - Human-like delay patterns

    Attributes:
        marketplace_name: Unique identifier (e.g. "ozon", "wildberries").
        base_url: Root URL of the marketplace.
        rate_limit: Maximum requests per second (baseline).
        max_retries: Number of retry attempts on failure.
    """

    marketplace_name: str
    base_url: str
    rate_limit: float = 1.0
    max_retries: int = 3

    def __init__(self) -> None:
        self._session_mgr = SessionManager(_get_proxy_rotator())
        self._behavior = HumanBehavior()

        # Adaptive rate: starts at configured rate, decreases on blocks
        self._current_rate = self.rate_limit
        self._min_rate = 0.1  # Floor: 1 request per 10 seconds
        self._consecutive_ok = 0
        self._last_request_at = 0.0

    # ------------------------------------------------------------------
    # Rate limiting (adaptive)
    # ------------------------------------------------------------------

    async def _enforce_rate_limit(self) -> None:
        """Wait with adaptive rate + human-like jitter.

        Rate slows down when blocks are detected,
        recovers gradually after 10 consecutive successes.
        """
        min_interval = 1.0 / self._current_rate
        elapsed = time.monotonic() - self._last_request_at

        if elapsed < min_interval:
            base_wait = min_interval - elapsed
            # Human jitter: ±30% of interval
            jitter = base_wait * 0.3 * (2 * random.random() - 1)
            await asyncio.sleep(max(0.1, base_wait + jitter))

        self._last_request_at = time.monotonic()

    def _on_success(self) -> None:
        """Track success — gradually recover rate after blocks."""
        self._consecutive_ok += 1
        if self._consecutive_ok >= 10 and self._current_rate < self.rate_limit:
            self._current_rate = min(self._current_rate * 1.2, self.rate_limit)
            self._consecutive_ok = 0
            logger.info(
                "rate_recovered",
                extra={
                    "marketplace": self.marketplace_name,
                    "new_rate": round(self._current_rate, 2),
                },
            )

    def _on_block(self, reason: str) -> None:
        """Track block — halve rate immediately."""
        self._consecutive_ok = 0
        old_rate = self._current_rate
        self._current_rate = max(self._current_rate * 0.5, self._min_rate)
        logger.warning(
            "rate_backed_off",
            extra={
                "marketplace": self.marketplace_name,
                "reason": reason,
                "old_rate": round(old_rate, 2),
                "new_rate": round(self._current_rate, 2),
            },
        )

    # ------------------------------------------------------------------
    # Session & proxy helpers
    # ------------------------------------------------------------------

    async def _get_session(self) -> ScrapingSession:
        """Get or create session for this marketplace."""
        return await self._session_mgr.get_or_create_session(self.marketplace_name)

    async def _get_proxy(self) -> str | None:
        """Get proxy URL from rotator."""
        session = await self._get_session()
        return await self._session_mgr.get_proxy_for_session(session)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def search(self, query: str, *, page: int = 1) -> list[ProductCreate]:
        """Search for products by text query.

        Args:
            query: Search string.
            page: Results page number (1-indexed).

        Returns:
            List of parsed products.
        """

    @abstractmethod
    async def get_product(self, product_id: str) -> ProductCreate:
        """Fetch full details for a single product.

        Args:
            product_id: Marketplace-specific product identifier.

        Returns:
            Parsed product data.

        Raises:
            ScraperError: If product cannot be fetched or parsed.
        """

    async def get_category(
        self,
        category_url: str,
        *,
        max_pages: int = 50,
    ) -> AsyncGenerator[ProductCreate, None]:
        """Iterate over all products in a category.

        Args:
            category_url: Full URL of the category page.
            max_pages: Safety limit to prevent infinite pagination.

        Yields:
            Parsed products one by one.
        """
        page = 1
        while page <= max_pages:
            products = await self._fetch_category_page(category_url, page)
            if not products:
                break
            for product in products:
                yield product
            page += 1

    async def _fetch_category_page(self, category_url: str, page: int) -> list[ProductCreate]:
        """Fetch a single page of category results. Override if needed."""
        return []

    async def close(self) -> None:
        """Release resources. Override in subclasses if needed."""


# ---------------------------------------------------------------------------
# HttpScraper (Fetcher — fast HTTP, no browser)
# ---------------------------------------------------------------------------


class HttpScraper(BaseScraper):
    """Scraper using Scrapling's AsyncFetcher (HTTP-only, no browser).

    Best for:
    - Sites with public JSON APIs (e.g. Wildberries)
    - Server-rendered HTML pages
    - Maximum speed (no browser overhead)

    Anti-detection:
    - TLS fingerprint impersonation via curl_cffi
    - Proxy rotation via ProxyRotator
    - Adaptive rate limiting with backoff on 429/403
    - Human-like jitter between requests
    """

    async def fetch_page(self, url: str) -> Selector:
        """Fetch HTML page via HTTP with anti-detection.

        Args:
            url: Target URL.

        Returns:
            Scrapling Selector (parsed page).

        Raises:
            ScraperError: After all retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            await self._enforce_rate_limit()

            try:
                proxy = await self._get_proxy()

                kwargs: dict[str, Any] = {
                    "stealthy_headers": True,
                    "follow_redirects": True,
                    "timeout": 30,
                }
                if proxy:
                    kwargs["proxy"] = proxy

                page = await AsyncFetcher.get(url, **kwargs)
                body = str(page.body) if hasattr(page, "body") else ""

                block_reason = _is_blocked(page.status, body)
                if block_reason:
                    self._on_block(block_reason)
                    logger.warning(
                        "http_blocked",
                        extra={
                            "url": url,
                            "reason": block_reason,
                            "status": page.status,
                            "attempt": attempt,
                        },
                    )
                    if attempt < self.max_retries:
                        await HumanBehavior.random_delay(5.0, 15.0)
                        continue

                if page.status != 200:
                    if attempt < self.max_retries:
                        await HumanBehavior.random_delay(3.0, 8.0)
                        continue

                self._on_success()
                return page

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "http_fetch_error",
                    extra={"url": url, "error": str(exc), "attempt": attempt},
                )
                if attempt < self.max_retries:
                    await HumanBehavior.random_delay(3.0, 10.0)

        raise ScraperError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}")

    async def fetch_json(self, url: str, *, params: dict | None = None) -> dict:
        """Fetch JSON from API endpoint with anti-detection.

        Args:
            url: API endpoint URL.
            params: Query parameters.

        Returns:
            Parsed JSON dict.
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            await self._enforce_rate_limit()

            try:
                full_url = f"{url}?{urlencode(params)}" if params else url
                proxy = await self._get_proxy()

                kwargs: dict[str, Any] = {
                    "stealthy_headers": True,
                    "follow_redirects": True,
                    "timeout": 30,
                }
                if proxy:
                    kwargs["proxy"] = proxy

                response = await AsyncFetcher.get(full_url, **kwargs)
                body_str = str(response.body) if hasattr(response, "body") else ""

                block_reason = _is_blocked(response.status, body_str)
                if block_reason:
                    self._on_block(block_reason)
                    if attempt < self.max_retries:
                        await HumanBehavior.random_delay(5.0, 15.0)
                        continue

                if response.status != 200:
                    if attempt < self.max_retries:
                        await HumanBehavior.random_delay(3.0, 8.0)
                        continue

                self._on_success()
                return json.loads(response.body)

            except (json.JSONDecodeError, ScraperError):
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "json_fetch_error",
                    extra={"url": url, "error": str(exc), "attempt": attempt},
                )
                if attempt < self.max_retries:
                    await HumanBehavior.random_delay(3.0, 10.0)

        raise ScraperError(
            f"JSON fetch failed: {url} after {self.max_retries} attempts: {last_error}"
        )


# ---------------------------------------------------------------------------
# DynamicScraper (StealthyFetcher — full browser with stealth)
# ---------------------------------------------------------------------------


class DynamicScraper(BaseScraper):
    """Scraper using Scrapling's StealthyFetcher (full browser).

    Best for:
    - JS-heavy sites (Ozon, Яндекс.Маркет)
    - Sites with Cloudflare / anti-bot JS challenges
    - Pages requiring interaction to load content

    Anti-detection stack (why each layer matters):

    Layer 1 — TLS fingerprint:
        StealthyFetcher uses a modified browser that produces a real
        Chrome JA3/JA4 hash, not a detectable library fingerprint.

    Layer 2 — Browser fingerprint:
        Canvas noise, WebGL spoofing, WebRTC blocking, consistent
        timezone/locale matching proxy geo.

    Layer 3 — Behavioral:
        page_action callback scrolls the page, adds random pauses.
        Without this, Ozon flags us even with perfect fingerprints.

    Layer 4 — IP reputation:
        Residential/mobile proxies via ProxyRotator. Datacenter IPs
        are instantly blocked by both Ozon and WB.

    Layer 5 — Session consistency:
        Same proxy + cookies for a sequence of requests. New identity
        per request is suspicious — real users browse multiple pages.
    """

    async def fetch_page(
        self,
        url: str,
        *,
        wait_selector: str | None = None,
        network_idle: bool = True,
        disable_resources: bool = True,
        scroll: bool = True,
    ) -> Selector:
        """Fetch page with browser rendering + human behavior simulation.

        The critical addition vs naive StealthyFetcher.fetch():
        We pass page_action that scrolls and pauses, simulating a real user.
        Without this, behavior-based detection flags us immediately.

        Args:
            url: Target URL.
            wait_selector: CSS selector to wait for before capturing HTML.
            network_idle: Wait until network activity settles.
            disable_resources: Block images/fonts for speed.
            scroll: Simulate scrolling (highly recommended for Ozon).

        Returns:
            Scrapling Selector with adaptive element tracking.

        Raises:
            ScraperError: After all retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            await self._enforce_rate_limit()

            try:
                proxy = await self._get_proxy()

                # Build config with scroll simulation + random headers
                antidetect = build_antidetect_config(
                    proxy_url=proxy,
                    scroll=scroll,
                    scroll_depth=0.5 + random.random() * 0.4,  # 50-90%
                    add_random_delay=True,
                )
                fetch_kwargs = antidetect.to_stealthy_kwargs()

                if wait_selector:
                    fetch_kwargs["wait_selector"] = wait_selector
                fetch_kwargs["network_idle"] = network_idle
                fetch_kwargs["disable_resources"] = disable_resources

                start = time.monotonic()
                page = await StealthyFetcher.async_fetch(url, **fetch_kwargs)
                elapsed_ms = (time.monotonic() - start) * 1000

                body = str(page.body) if hasattr(page, "body") else ""
                block_reason = _is_blocked(page.status, body)

                if block_reason:
                    self._on_block(block_reason)
                    self._report_proxy_failure(proxy)
                    logger.warning(
                        "dynamic_blocked",
                        extra={
                            "url": url,
                            "reason": block_reason,
                            "status": page.status,
                            "attempt": attempt,
                        },
                    )
                    if attempt < self.max_retries:
                        await HumanBehavior.random_delay(10.0, 30.0)
                        continue

                if page.status != 200:
                    if attempt < self.max_retries:
                        await HumanBehavior.random_delay(5.0, 15.0)
                        continue

                self._on_success()
                self._report_proxy_success(proxy, elapsed_ms)

                session = await self._get_session()
                session.record_visit(url)

                logger.info(
                    "dynamic_fetch_ok",
                    extra={
                        "url": url,
                        "marketplace": self.marketplace_name,
                        "attempt": attempt,
                        "elapsed_ms": round(elapsed_ms),
                    },
                )
                return page

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "dynamic_fetch_error",
                    extra={"url": url, "error": str(exc), "attempt": attempt},
                )
                if attempt < self.max_retries:
                    await HumanBehavior.random_delay(5.0, 20.0)

        raise ScraperError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}")

    async def fetch_with_session(
        self,
        urls: list[str],
        *,
        wait_selector: str | None = None,
        network_idle: bool = True,
        warmup: bool = True,
    ) -> list[Selector]:
        """Fetch multiple pages in a single browser session.

        Key anti-detection benefits of session reuse:
        - Same cookies/localStorage across requests (consistent identity)
        - Realistic navigation history (referers chain naturally)
        - One proxy for entire session (no suspicious IP switching)
        - Warmup: visit homepage first to establish legitimate session

        Args:
            urls: List of URLs to fetch.
            wait_selector: CSS selector to wait for on each page.
            network_idle: Wait until network is idle.
            warmup: Visit marketplace homepage first.

        Returns:
            List of Selectors in the same order as input URLs.
        """
        results: dict[str, Selector] = {}
        proxy = await self._get_proxy()

        session_kwargs: dict[str, Any] = {
            "headless": True,
            "block_webrtc": True,
        }
        if proxy:
            session_kwargs["proxy"] = proxy

        async with AsyncStealthySession(**session_kwargs) as session:
            # WARMUP: visit homepage first to build cookies
            if warmup:
                logger.info(
                    "session_warmup",
                    extra={"marketplace": self.marketplace_name},
                )
                try:
                    await session.fetch(
                        self.base_url,
                        network_idle=True,
                        google_search=True,
                    )
                    await HumanBehavior.random_delay(3.0, 8.0)
                except Exception as exc:
                    logger.debug("warmup_failed", extra={"error": str(exc)})

            for url in urls:
                await self._enforce_rate_limit()

                fetch_kwargs: dict[str, Any] = {
                    "network_idle": network_idle,
                    "disable_resources": True,
                }
                if wait_selector:
                    fetch_kwargs["wait_selector"] = wait_selector

                try:
                    page = await session.fetch(url, **fetch_kwargs)

                    body = str(page.body) if hasattr(page, "body") else ""
                    block_reason = _is_blocked(page.status, body)

                    if block_reason:
                        self._on_block(block_reason)
                        await HumanBehavior.random_delay(10.0, 25.0)
                    else:
                        self._on_success()

                    results[url] = page

                    # Simulate reading the page
                    await HumanBehavior.random_delay(2.0, 6.0)

                except Exception as exc:
                    logger.error(
                        "session_fetch_error",
                        extra={"url": url, "error": str(exc)},
                    )
                    raise ScraperError(f"Session fetch failed for {url}: {exc}") from exc

        return [results[url] for url in urls if url in results]

    # ------------------------------------------------------------------
    # Proxy reporting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _report_proxy_success(proxy_url: str | None, elapsed_ms: float) -> None:
        """Report successful request to proxy rotator."""
        if not proxy_url:
            return
        rotator = _get_proxy_rotator()
        for entry in rotator._proxies:
            if entry.url == proxy_url:
                rotator.report_success(entry, elapsed_ms)
                return

    @staticmethod
    def _report_proxy_failure(proxy_url: str | None) -> None:
        """Report failed request to proxy rotator."""
        if not proxy_url:
            return
        rotator = _get_proxy_rotator()
        for entry in rotator._proxies:
            if entry.url == proxy_url:
                rotator.report_failure(entry)
                return


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ScraperError(Exception):
    """Base exception for scraper failures."""


class ProductNotFoundError(ScraperError):
    """Raised when a product cannot be found on the marketplace."""


class RateLimitError(ScraperError):
    """Raised when the marketplace rate-limits our requests."""


class ParsingError(ScraperError):
    """Raised when page content cannot be parsed into product data."""


class BlockedError(ScraperError):
    """Raised when the marketplace has blocked us (captcha, 403, etc.)."""
