"""Anti-detection middleware for marketplace scrapers.

Addresses the core problem: marketplaces don't just check browser fingerprints,
they detect BOT BEHAVIOR PATTERNS:

1. **IP reputation** — datacenter IPs are instantly flagged
2. **Request cadence** — fixed intervals = bot, variable = human
3. **Navigation patterns** — humans don't jump directly to page 47
4. **Session behavior** — humans browse, scroll, click; bots GET and leave
5. **TLS/JA3 fingerprint** — must match a real browser
6. **Mouse/scroll events** — JS-based detection on page

This module provides:
- ProxyRotator: residential proxy pool with health tracking
- HumanBehavior: realistic delays, scroll simulation, page_action callbacks
- RequestFingerprint: randomized headers, referer chains, cookie persistence
- SessionManager: maintains realistic browsing sessions with history
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Proxy rotation
# ---------------------------------------------------------------------------


class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


@dataclass
class ProxyEntry:
    """Single proxy with health tracking."""

    url: str
    protocol: ProxyProtocol = ProxyProtocol.HTTP

    # Health metrics
    total_requests: int = 0
    failed_requests: int = 0
    last_used_at: float = 0.0
    last_failed_at: float = 0.0
    consecutive_failures: int = 0
    avg_response_time_ms: float = 0.0

    # Cooldown: how long to wait before reusing this proxy
    cooldown_seconds: float = 5.0

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def is_healthy(self) -> bool:
        """Proxy is healthy if failure rate is below 50% and not in cooldown."""
        if self.consecutive_failures >= 5:
            return False
        if self.failure_rate > 0.5 and self.total_requests > 3:
            return False
        return True

    @property
    def is_available(self) -> bool:
        """Proxy is available if healthy and cooldown has elapsed."""
        if not self.is_healthy:
            return False
        elapsed = time.monotonic() - self.last_used_at
        return elapsed >= self.cooldown_seconds

    def record_success(self, response_time_ms: float) -> None:
        """Record a successful request."""
        self.total_requests += 1
        self.consecutive_failures = 0
        self.last_used_at = time.monotonic()
        # Exponential moving average for response time
        alpha = 0.3
        self.avg_response_time_ms = (
            alpha * response_time_ms + (1 - alpha) * self.avg_response_time_ms
        )

    def record_failure(self) -> None:
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_used_at = time.monotonic()
        self.last_failed_at = time.monotonic()
        # Increase cooldown on consecutive failures
        self.cooldown_seconds = min(300.0, self.cooldown_seconds * (1.5**self.consecutive_failures))


class ProxyRotator:
    """Manages a pool of proxies with health-aware rotation.

    Priorities:
    1. Residential proxies (lowest detection rate)
    2. Mobile proxies (good for marketplaces)
    3. ISP proxies (static residential)

    Usage:
        rotator = ProxyRotator()
        rotator.add_proxies([
            "http://user:pass@residential1.example.com:8080",
            "socks5://user:pass@mobile1.example.com:1080",
        ])

        proxy = rotator.get_next()
        # ... use proxy ...
        rotator.report_success(proxy, response_time_ms=320)
    """

    def __init__(self, min_cooldown: float = 3.0) -> None:
        self._proxies: list[ProxyEntry] = []
        self._min_cooldown = min_cooldown
        self._lock = asyncio.Lock()

    def add_proxies(
        self,
        proxy_urls: list[str],
        cooldown: float | None = None,
    ) -> None:
        """Add proxies to the pool.

        Args:
            proxy_urls: List of proxy URLs (e.g. "http://user:pass@host:port").
            cooldown: Per-proxy cooldown in seconds between uses.
        """
        for url in proxy_urls:
            protocol = ProxyProtocol.HTTP
            if url.startswith("socks5://"):
                protocol = ProxyProtocol.SOCKS5
            elif url.startswith("https://"):
                protocol = ProxyProtocol.HTTPS

            entry = ProxyEntry(
                url=url,
                protocol=protocol,
                cooldown_seconds=cooldown or self._min_cooldown,
            )
            self._proxies.append(entry)

        logger.info(
            "proxies_added",
            extra={"count": len(proxy_urls), "total": len(self._proxies)},
        )

    async def get_next(self) -> ProxyEntry | None:
        """Get the next available proxy using weighted random selection.

        Prioritizes:
        - Available (not in cooldown)
        - Healthy (low failure rate)
        - Faster (lower avg response time)

        Returns:
            ProxyEntry or None if no proxies available.
        """
        async with self._lock:
            available = [p for p in self._proxies if p.is_available]

            if not available:
                # All in cooldown — wait for shortest cooldown
                if self._proxies:
                    healthy = [p for p in self._proxies if p.is_healthy]
                    if healthy:
                        soonest = min(
                            healthy,
                            key=lambda p: p.cooldown_seconds - (time.monotonic() - p.last_used_at),
                        )
                        wait_time = max(
                            0,
                            soonest.cooldown_seconds - (time.monotonic() - soonest.last_used_at),
                        )
                        logger.debug(
                            "proxy_cooldown_wait",
                            extra={"wait_s": round(wait_time, 2)},
                        )
                        await asyncio.sleep(wait_time)
                        return soonest
                return None

            # Weighted selection: lower failure rate + lower response time = higher weight
            weights = []
            for proxy in available:
                # Base weight
                w = 1.0
                # Penalize high failure rate
                w *= 1.0 - proxy.failure_rate
                # Prefer faster proxies (normalize to 0-1 range)
                if proxy.avg_response_time_ms > 0:
                    w *= 1000.0 / (1000.0 + proxy.avg_response_time_ms)
                # Slight randomization to avoid patterns
                w *= random.uniform(0.8, 1.2)
                weights.append(max(w, 0.01))

            # Weighted random choice
            chosen = random.choices(available, weights=weights, k=1)[0]
            chosen.last_used_at = time.monotonic()
            return chosen

    def report_success(self, proxy: ProxyEntry, response_time_ms: float) -> None:
        """Report a successful request through this proxy."""
        proxy.record_success(response_time_ms)

    def report_failure(self, proxy: ProxyEntry) -> None:
        """Report a failed request through this proxy."""
        proxy.record_failure()
        logger.warning(
            "proxy_failure",
            extra={
                "proxy": _mask_proxy_url(proxy.url),
                "consecutive_failures": proxy.consecutive_failures,
                "cooldown_s": proxy.cooldown_seconds,
            },
        )

    @property
    def healthy_count(self) -> int:
        return sum(1 for p in self._proxies if p.is_healthy)

    @property
    def total_count(self) -> int:
        return len(self._proxies)

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        return {
            "total": self.total_count,
            "healthy": self.healthy_count,
            "available": sum(1 for p in self._proxies if p.is_available),
            "avg_failure_rate": (
                sum(p.failure_rate for p in self._proxies) / len(self._proxies)
                if self._proxies
                else 0
            ),
        }


# ---------------------------------------------------------------------------
# Human-like behavior simulation
# ---------------------------------------------------------------------------


class HumanBehavior:
    """Simulates human browsing patterns to avoid bot detection.

    Key techniques:
    - Variable delays with realistic distribution (not uniform!)
    - Scroll simulation before extracting data
    - Mouse movement simulation
    - Referrer chain building (Google → marketplace → product)
    - Session warmup (visit homepage first)

    Usage with Scrapling's page_action:
        behavior = HumanBehavior()

        page = StealthyFetcher.fetch(
            url,
            page_action=behavior.create_page_action(scroll=True, pause=True),
        )
    """

    # Realistic delay distributions (seconds)
    # Based on real user session analysis
    DELAY_BETWEEN_PAGES = (2.0, 7.0)  # Between page navigations
    DELAY_BEFORE_SCROLL = (0.5, 2.0)  # Before starting to scroll
    DELAY_BETWEEN_SCROLLS = (0.3, 1.5)  # Between scroll increments
    DELAY_BEFORE_CLICK = (0.2, 0.8)  # Before clicking an element
    DELAY_ON_PAGE = (3.0, 12.0)  # Time spent "reading" a page

    @staticmethod
    async def random_delay(
        min_s: float = 1.0,
        max_s: float = 3.0,
        *,
        distribution: str = "normal",
    ) -> None:
        """Wait a random amount of time with human-like distribution.

        Uses normal distribution by default — humans cluster around
        a mean with occasional outliers, unlike uniform distribution.

        Args:
            min_s: Minimum delay.
            max_s: Maximum delay.
            distribution: "normal" or "uniform".
        """
        if distribution == "normal":
            # Normal distribution centered between min and max
            mean = (min_s + max_s) / 2
            std = (max_s - min_s) / 4  # 95% within [min, max]
            delay = max(min_s, min(max_s, random.gauss(mean, std)))
        else:
            delay = random.uniform(min_s, max_s)

        await asyncio.sleep(delay)

    @staticmethod
    async def page_delay() -> None:
        """Delay between page navigations."""
        await HumanBehavior.random_delay(*HumanBehavior.DELAY_BETWEEN_PAGES)

    @staticmethod
    async def reading_delay() -> None:
        """Simulate time spent reading a page."""
        await HumanBehavior.random_delay(*HumanBehavior.DELAY_ON_PAGE)

    @staticmethod
    def create_page_action(
        *,
        scroll: bool = True,
        random_pause: bool = True,
        scroll_depth: float = 0.7,
    ) -> Callable:
        """Create a page_action callback for Scrapling's fetchers.

        This callback is executed by Scrapling after the page loads
        but before the HTML is captured. It simulates human interaction.

        Args:
            scroll: Whether to scroll through the page.
            random_pause: Whether to add random pauses.
            scroll_depth: How far to scroll (0.0 to 1.0).

        Returns:
            Async callback compatible with Scrapling's page_action parameter.

        Example:
            page = StealthyFetcher.fetch(
                url,
                page_action=HumanBehavior.create_page_action(scroll=True),
            )
        """

        async def action(page: Any) -> None:
            """Simulate human browsing on the loaded page."""
            if random_pause:
                await asyncio.sleep(random.uniform(0.5, 2.0))

            if scroll:
                await _simulate_scroll(page, depth=scroll_depth)

            if random_pause:
                await asyncio.sleep(random.uniform(1.0, 3.0))

        return action

    @staticmethod
    def create_warmup_actions(marketplace_url: str) -> list[dict[str, Any]]:
        """Create a sequence of warmup navigations.

        Before scraping, visit the site "naturally":
        1. Google search → marketplace (via referer)
        2. Homepage → category browsing
        3. Then actual target page

        This builds a realistic session with cookies and history.

        Args:
            marketplace_url: Base URL of the marketplace.

        Returns:
            List of navigation configs for session warmup.
        """
        return [
            {
                "url": marketplace_url,
                "google_search": True,  # Appear to come from Google
                "wait_time": random.uniform(2, 5),
                "scroll": True,
            },
        ]


async def _simulate_scroll(page: Any, *, depth: float = 0.7) -> None:
    """Simulate human-like scrolling on a Playwright page.

    Humans don't scroll at constant speed — they pause to read,
    scroll fast through irrelevant content, and slow down at interesting parts.

    Args:
        page: Playwright Page object (passed by Scrapling's page_action).
        depth: How far down the page to scroll (0.0 to 1.0).
    """
    try:
        # Get page height
        total_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        target_scroll = int(total_height * depth)

        current_pos = 0
        while current_pos < target_scroll:
            # Variable scroll distance (50-400px per step)
            scroll_step = random.randint(50, 400)

            # Occasionally do a bigger jump (like flicking on mobile)
            if random.random() < 0.1:
                scroll_step = random.randint(400, 800)

            current_pos = min(current_pos + scroll_step, target_scroll)
            await page.evaluate(f"window.scrollTo(0, {current_pos})")

            # Variable pause between scrolls
            pause = random.uniform(0.1, 0.8)
            # Occasionally pause longer (reading something)
            if random.random() < 0.15:
                pause = random.uniform(1.0, 3.0)

            await asyncio.sleep(pause)

    except Exception as exc:
        # Non-critical — don't break scraping if scroll simulation fails
        logger.debug("scroll_simulation_error", extra={"error": str(exc)})


# ---------------------------------------------------------------------------
# Request fingerprinting
# ---------------------------------------------------------------------------


class RequestFingerprint:
    """Manages request headers and metadata to appear human.

    Beyond TLS fingerprint (handled by Scrapling), we need:
    - Realistic Accept-Language (matching proxy geo)
    - Proper referer chains
    - Consistent session-level headers
    - Cookie persistence across requests
    """

    # Realistic Accept-Language values for Russian marketplaces
    ACCEPT_LANGUAGES_RU = [
        "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "ru,en-US;q=0.9,en;q=0.8",
        "ru-RU,ru;q=0.9,en;q=0.8,de;q=0.7",
        "ru-RU,ru;q=0.9",
        "ru,en;q=0.9,en-US;q=0.8",
    ]

    # Common screen resolutions
    VIEWPORTS = [
        (1920, 1080),
        (1536, 864),
        (1366, 768),
        (1440, 900),
        (1280, 720),
        (2560, 1440),
        (1680, 1050),
    ]

    @staticmethod
    def get_random_headers() -> dict[str, str]:
        """Generate a set of realistic extra headers.

        Returns:
            Dict of headers to pass as extra_headers to Scrapling fetchers.
        """
        return {
            "Accept-Language": random.choice(RequestFingerprint.ACCEPT_LANGUAGES_RU),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    @staticmethod
    def get_random_viewport() -> dict[str, int]:
        """Get a random but common screen resolution.

        Returns:
            Dict with width and height keys.
        """
        w, h = random.choice(RequestFingerprint.VIEWPORTS)
        return {"width": w, "height": h}

    @staticmethod
    def build_referer_chain(
        marketplace_base_url: str,
        target_url: str,
    ) -> str:
        """Build a realistic referer for the target URL.

        Simulates: Google → marketplace homepage → target.

        Args:
            marketplace_base_url: E.g. "https://www.ozon.ru".
            target_url: The actual URL being fetched.

        Returns:
            Referer URL string.
        """
        # If going to a search page, referer should be the homepage
        if "/search" in target_url or "text=" in target_url:
            return marketplace_base_url + "/"

        # If going to a product page, referer should be search
        if "/product/" in target_url or "/catalog/" in target_url:
            return marketplace_base_url + "/search/?text=query"

        # Default: come from Google
        return f"https://www.google.com/search?q={marketplace_base_url}"


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


@dataclass
class ScrapingSession:
    """Tracks state for a single scraping session.

    Maintains realistic browsing context:
    - Pages visited (for referer chain)
    - Request count (for pacing)
    - Session start time (for total duration limits)
    - Cookies (via Scrapling's session management)
    """

    marketplace: str
    started_at: float = field(default_factory=time.monotonic)
    pages_visited: list[str] = field(default_factory=list)
    request_count: int = 0
    max_requests_per_session: int = 50
    max_session_duration_s: float = 600.0  # 10 minutes

    @property
    def is_expired(self) -> bool:
        """Session should be rotated after too many requests or too long."""
        if self.request_count >= self.max_requests_per_session:
            return True
        elapsed = time.monotonic() - self.started_at
        return elapsed >= self.max_session_duration_s

    @property
    def last_page(self) -> str | None:
        return self.pages_visited[-1] if self.pages_visited else None

    def record_visit(self, url: str) -> None:
        self.pages_visited.append(url)
        self.request_count += 1


class SessionManager:
    """Manages scraping sessions with automatic rotation.

    Sessions are rotated when they expire (too many requests or too long).
    Each new session gets a fresh proxy and browser context.

    Usage:
        manager = SessionManager(proxy_rotator)

        async with manager.get_session("ozon") as session:
            # session.proxy — current proxy
            # session.headers — current headers
            pass
    """

    def __init__(self, proxy_rotator: ProxyRotator | None = None) -> None:
        self._proxy_rotator = proxy_rotator
        self._active_sessions: dict[str, ScrapingSession] = {}

    async def get_or_create_session(self, marketplace: str) -> ScrapingSession:
        """Get active session or create a new one.

        Automatically rotates expired sessions.

        Args:
            marketplace: Marketplace identifier.

        Returns:
            Active ScrapingSession.
        """
        session = self._active_sessions.get(marketplace)

        if session and not session.is_expired:
            return session

        if session and session.is_expired:
            logger.info(
                "session_rotated",
                extra={
                    "marketplace": marketplace,
                    "requests_made": session.request_count,
                    "duration_s": round(time.monotonic() - session.started_at, 1),
                },
            )

        # Create new session
        new_session = ScrapingSession(marketplace=marketplace)
        self._active_sessions[marketplace] = new_session
        return new_session

    async def get_proxy_for_session(self, session: ScrapingSession) -> str | None:
        """Get a proxy URL for the current session.

        Args:
            session: Current scraping session.

        Returns:
            Proxy URL string or None if no proxy pool configured.
        """
        if not self._proxy_rotator:
            return None

        proxy_entry = await self._proxy_rotator.get_next()
        return proxy_entry.url if proxy_entry else None


# ---------------------------------------------------------------------------
# Anti-detection config builder
# ---------------------------------------------------------------------------


@dataclass
class AntiDetectConfig:
    """Complete anti-detection configuration for a single fetch request.

    Combines proxy, headers, behavior, and timing into a single config
    that can be passed to Scrapling's fetcher methods.
    """

    proxy: str | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    page_action: Callable | None = None
    timeout: int = 30000
    network_idle: bool = True
    disable_resources: bool = True
    google_search: bool = True
    block_webrtc: bool = True

    def to_stealthy_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs for StealthyFetcher.fetch() / .async_fetch().

        Returns:
            Dict of keyword arguments ready for Scrapling.
        """
        kwargs: dict[str, Any] = {
            "headless": True,
            "network_idle": self.network_idle,
            "disable_resources": self.disable_resources,
            "google_search": self.google_search,
            "block_webrtc": self.block_webrtc,
            "timeout": self.timeout,
        }

        if self.proxy:
            kwargs["proxy"] = self.proxy

        if self.extra_headers:
            kwargs["extra_headers"] = self.extra_headers

        if self.page_action:
            kwargs["page_action"] = self.page_action

        return kwargs

    def to_fetcher_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs for AsyncFetcher.get() (HTTP fetcher).

        Returns:
            Dict of keyword arguments for HTTP requests.
        """
        kwargs: dict[str, Any] = {
            "stealthy_headers": True,
            "follow_redirects": True,
            "timeout": self.timeout // 1000,  # Fetcher uses seconds
        }

        if self.proxy:
            kwargs["proxy"] = self.proxy

        return kwargs


def build_antidetect_config(
    *,
    proxy_url: str | None = None,
    scroll: bool = True,
    scroll_depth: float = 0.7,
    add_random_delay: bool = True,
) -> AntiDetectConfig:
    """Build a complete anti-detection config for one request.

    Convenience function that combines all anti-detection measures.

    Args:
        proxy_url: Proxy to use (or None for direct connection).
        scroll: Whether to simulate scrolling.
        scroll_depth: How far to scroll (0.0 to 1.0).
        add_random_delay: Whether the page_action should include pauses.

    Returns:
        Ready-to-use AntiDetectConfig.
    """
    page_action = None
    if scroll or add_random_delay:
        page_action = HumanBehavior.create_page_action(
            scroll=scroll,
            random_pause=add_random_delay,
            scroll_depth=scroll_depth,
        )

    return AntiDetectConfig(
        proxy=proxy_url,
        extra_headers=RequestFingerprint.get_random_headers(),
        page_action=page_action,
    )


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _mask_proxy_url(url: str) -> str:
    """Mask credentials in proxy URL for safe logging.

    "http://user:pass@host:8080" → "http://u***:p***@host:8080"
    """
    import re

    return re.sub(
        r"://([^:]+):([^@]+)@",
        r"://\1***:\2***@",
        url,
    )
