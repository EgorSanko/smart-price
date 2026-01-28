"""Utility functions for marketplace scrapers.

This module provides common utilities for scraping including:
- User-Agent rotation
- Random delays
- Retry decorators
- Proxy management
- Price parsing
- Text cleaning
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from functools import wraps
from typing import Any, Callable, TypeVar

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# User-Agent Rotation
# ============================================================================

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

MOBILE_USER_AGENTS = [
    # iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    # Android
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
]


def get_random_user_agent(mobile: bool = False) -> str:
    """Get a random User-Agent string.

    Args:
        mobile: If True, return a mobile User-Agent.

    Returns:
        Random User-Agent string.
    """
    agents = MOBILE_USER_AGENTS if mobile else USER_AGENTS
    return random.choice(agents)


def get_random_headers(
    mobile: bool = False,
    referer: str | None = None,
    accept_language: str = "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
) -> dict[str, str]:
    """Get randomized HTTP headers.

    Args:
        mobile: Use mobile User-Agent.
        referer: Optional referer URL.
        accept_language: Accept-Language header value.

    Returns:
        Dictionary of HTTP headers.
    """
    headers = {
        "User-Agent": get_random_user_agent(mobile),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": accept_language,
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none" if not referer else "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": "1",
    }

    if referer:
        headers["Referer"] = referer

    # Randomize some headers
    if random.random() > 0.5:
        headers["Sec-CH-UA"] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        headers["Sec-CH-UA-Mobile"] = "?1" if mobile else "?0"
        headers["Sec-CH-UA-Platform"] = '"Android"' if mobile else '"Windows"'

    return headers


# ============================================================================
# Random Delays
# ============================================================================


async def random_delay(
    min_seconds: float = 0.5,
    max_seconds: float = 2.0,
) -> None:
    """Wait for a random amount of time.

    Args:
        min_seconds: Minimum delay in seconds.
        max_seconds: Maximum delay in seconds.
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def human_like_delay() -> None:
    """Simulate human-like delay between actions.

    Uses a normal distribution centered around 1.5 seconds.
    """
    # Normal distribution with mean=1.5, std=0.5, clamped to [0.3, 5.0]
    delay = max(0.3, min(5.0, random.gauss(1.5, 0.5)))
    await asyncio.sleep(delay)


class RateLimiter:
    """Token bucket rate limiter for async operations.

    Example:
        >>> limiter = RateLimiter(rate=2.0, burst=5)
        >>> async with limiter:
        ...     await fetch_data()
    """

    def __init__(self, rate: float = 1.0, burst: int = 1) -> None:
        """Initialize rate limiter.

        Args:
            rate: Requests per second.
            burst: Maximum burst size.
        """
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_update = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_update
            self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
            self._last_update = now

            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


# ============================================================================
# Retry Decorators
# ============================================================================


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts.
        min_wait: Minimum wait time between retries.
        max_wait: Maximum wait time between retries.
        exceptions: Tuple of exceptions to retry on.

    Returns:
        Decorated function.

    Example:
        >>> @with_retry(max_attempts=3)
        ... async def fetch_data():
        ...     ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait_time = min(
                            max_wait,
                            min_wait * (2 ** (attempt - 1)) + random.uniform(0, 1),
                        )
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.1fs",
                            attempt,
                            max_attempts,
                            func.__name__,
                            str(e),
                            wait_time,
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            "All %d attempts failed for %s: %s",
                            max_attempts,
                            func.__name__,
                            str(e),
                        )

            raise last_exception  # type: ignore

        return wrapper

    return decorator


def create_retry_decorator(
    max_attempts: int = 3,
    exceptions: tuple = (Exception,),
):
    """Create a tenacity retry decorator with custom settings.

    Args:
        max_attempts: Maximum retry attempts.
        exceptions: Exceptions to retry on.

    Returns:
        Configured retry decorator.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10) + wait_random(0, 1),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )


# ============================================================================
# Price Parsing
# ============================================================================


def parse_price(price_str: str | None) -> float | None:
    """Parse price string to float.

    Handles various formats:
    - "1 234 ₽" -> 1234.0
    - "1,234.56" -> 1234.56
    - "1.234,56" -> 1234.56 (European format)
    - "от 999 ₽" -> 999.0

    Args:
        price_str: Price string in various formats.

    Returns:
        Price as float or None if parsing fails.
    """
    if not price_str:
        return None

    # Remove "от", "до", "от " prefix
    price_str = re.sub(r"^(от|до|from|to)\s*", "", price_str, flags=re.IGNORECASE)

    # Remove currency symbols and whitespace
    cleaned = re.sub(r"[₽$€£¥\s\u00a0]", "", price_str)

    # Handle different decimal separators
    # If we have both . and ,, determine which is decimal
    if "." in cleaned and "," in cleaned:
        # Assume last separator is decimal
        if cleaned.rfind(".") > cleaned.rfind(","):
            # 1,234.56 format
            cleaned = cleaned.replace(",", "")
        else:
            # 1.234,56 format
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        # Check if comma is decimal separator (e.g., "12,99")
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    # Remove any remaining non-numeric characters except decimal point
    cleaned = re.sub(r"[^\d.]", "", cleaned)

    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        logger.warning("Failed to parse price: %s", price_str)
        return None


def format_price(price: float, currency: str = "₽") -> str:
    """Format price for display.

    Args:
        price: Price value.
        currency: Currency symbol.

    Returns:
        Formatted price string.
    """
    # Format with space as thousands separator
    formatted = f"{price:,.0f}".replace(",", " ")
    return f"{formatted} {currency}"


# ============================================================================
# Text Cleaning
# ============================================================================


def clean_text(text: str | None) -> str:
    """Clean and normalize text.

    - Remove extra whitespace
    - Remove HTML entities
    - Normalize quotes
    - Strip leading/trailing whitespace

    Args:
        text: Input text.

    Returns:
        Cleaned text.
    """
    if not text:
        return ""

    # Decode HTML entities
    import html

    text = html.unescape(text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")

    return text.strip()


def extract_numbers(text: str) -> list[int]:
    """Extract all numbers from text.

    Args:
        text: Input text.

    Returns:
        List of extracted integers.
    """
    return [int(n) for n in re.findall(r"\d+", text)]


def extract_product_id(url: str) -> str | None:
    """Extract product ID from marketplace URL.

    Supports:
    - Ozon: /product/name-123456/
    - Wildberries: /catalog/123456/detail.aspx
    - Yandex.Market: /product--name/123456

    Args:
        url: Product URL.

    Returns:
        Extracted product ID or None.
    """
    patterns = [
        r"/product/[^/]*?(\d+)/?",  # Ozon
        r"/catalog/(\d+)/",  # Wildberries
        r"/product--[^/]+/(\d+)",  # Yandex.Market
        r"[?&](?:sku|id|nm)=(\d+)",  # Query params
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


# ============================================================================
# Proxy Management
# ============================================================================


class ProxyRotator:
    """Rotate through a list of proxy URLs.

    Example:
        >>> rotator = ProxyRotator([
        ...     "http://proxy1:8080",
        ...     "http://proxy2:8080",
        ... ])
        >>> proxy = rotator.get_next()
    """

    def __init__(self, proxies: list[str] | None = None) -> None:
        """Initialize proxy rotator.

        Args:
            proxies: List of proxy URLs.
        """
        self._proxies = proxies or []
        self._index = 0
        self._failed: set[str] = set()

    def get_next(self) -> str | None:
        """Get next proxy in rotation.

        Returns:
            Proxy URL or None if no proxies available.
        """
        if not self._proxies:
            return None

        available = [p for p in self._proxies if p not in self._failed]
        if not available:
            # Reset failed proxies if all have failed
            self._failed.clear()
            available = self._proxies

        proxy = available[self._index % len(available)]
        self._index += 1
        return proxy

    def mark_failed(self, proxy: str) -> None:
        """Mark a proxy as failed.

        Args:
            proxy: Proxy URL that failed.
        """
        self._failed.add(proxy)
        logger.warning("Proxy marked as failed: %s", proxy)

    def mark_success(self, proxy: str) -> None:
        """Mark a proxy as working (remove from failed).

        Args:
            proxy: Proxy URL that succeeded.
        """
        self._failed.discard(proxy)

    @property
    def available_count(self) -> int:
        """Number of available (non-failed) proxies."""
        return len(self._proxies) - len(self._failed)


# ============================================================================
# URL Utilities
# ============================================================================


def normalize_url(url: str) -> str:
    """Normalize URL by removing tracking parameters.

    Args:
        url: Input URL.

    Returns:
        Cleaned URL without tracking params.
    """
    from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

    # Parameters to remove
    tracking_params = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "ref",
        "from",
        "yclid",
        "gclid",
        "fbclid",
        "_openstat",
        "ymclid",
    }

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    # Remove tracking parameters
    cleaned_query = {k: v for k, v in query.items() if k.lower() not in tracking_params}

    # Rebuild URL
    new_query = urlencode(cleaned_query, doseq=True)
    cleaned = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, "")
    )

    return cleaned


def build_url(base: str, path: str = "", params: dict[str, Any] | None = None) -> str:
    """Build URL with path and query parameters.

    Args:
        base: Base URL.
        path: URL path.
        params: Query parameters.

    Returns:
        Complete URL.
    """
    from urllib.parse import urlencode, urljoin

    url = urljoin(base, path)

    if params:
        # Filter None values
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(filtered)}"

    return url
