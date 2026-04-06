"""Tests for base scraper framework.

Tests cover:
- Adaptive rate limiting (backoff on blocks, recovery on success)
- Block detection integration
- Proxy rotation integration
- HttpScraper fetch with mocked responses
- DynamicScraper fetch with mocked StealthyFetcher
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.test_scrapers.conftest import (
    BLOCKED_RESPONSE_403,
    CAPTCHA_RESPONSE,
    WB_SEARCH_JSON,
    MockSelector,
)


# ---------------------------------------------------------------------------
# Concrete test scraper (minimal implementation for testing base logic)
# ---------------------------------------------------------------------------


class _TestHttpScraper:
    """Minimal HttpScraper subclass for testing."""

    marketplace_name = "test_http"
    base_url = "https://test.com"
    rate_limit = 100.0  # Fast for tests
    max_retries = 2

    async def search(self, query, *, page=1):
        return []

    async def get_product(self, product_id):
        return None


class _TestDynamicScraper:
    """Minimal DynamicScraper subclass for testing."""

    marketplace_name = "test_dynamic"
    base_url = "https://test.com"
    rate_limit = 100.0
    max_retries = 2

    async def search(self, query, *, page=1):
        return []

    async def get_product(self, product_id):
        return None


# ---------------------------------------------------------------------------
# Adaptive rate limiting
# ---------------------------------------------------------------------------


class TestAdaptiveRateLimiting:
    """Tests for adaptive rate control in BaseScraper."""

    def _make_scraper(self):
        """Create a BaseScraper-like object for testing rate logic."""
        # We test rate logic directly on a scraper instance
        # Import here to allow patching
        from app.scrapers.base import HttpScraper

        class TestScraper(HttpScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 10.0  # 10 req/s baseline
            max_retries = 1

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        with patch("app.scrapers.base._get_proxy_rotator"):
            scraper = TestScraper()
        return scraper

    def test_initial_rate(self) -> None:
        scraper = self._make_scraper()
        assert scraper._current_rate == 10.0

    def test_rate_halves_on_block(self) -> None:
        scraper = self._make_scraper()
        scraper._on_block("http_403")

        assert scraper._current_rate == pytest.approx(5.0)

    def test_rate_halves_multiple_times(self) -> None:
        scraper = self._make_scraper()
        scraper._on_block("captcha")
        scraper._on_block("rate_limited")

        assert scraper._current_rate == pytest.approx(2.5)

    def test_rate_does_not_go_below_minimum(self) -> None:
        scraper = self._make_scraper()
        for _ in range(20):
            scraper._on_block("blocked")

        assert scraper._current_rate >= scraper._min_rate

    def test_rate_recovers_after_successes(self) -> None:
        scraper = self._make_scraper()
        scraper._on_block("http_403")  # Rate → 5.0

        for _ in range(10):
            scraper._on_success()

        # Should have recovered: 5.0 * 1.2 = 6.0
        assert scraper._current_rate == pytest.approx(6.0)

    def test_rate_does_not_exceed_baseline(self) -> None:
        scraper = self._make_scraper()
        for _ in range(100):
            scraper._on_success()

        assert scraper._current_rate <= scraper.rate_limit

    def test_block_resets_consecutive_counter(self) -> None:
        scraper = self._make_scraper()
        for _ in range(5):
            scraper._on_success()
        assert scraper._consecutive_ok == 5

        scraper._on_block("blocked")
        assert scraper._consecutive_ok == 0


# ---------------------------------------------------------------------------
# HttpScraper with mocked fetcher
# ---------------------------------------------------------------------------


class TestHttpScraper:
    """Tests for HttpScraper.fetch_page and fetch_json."""

    @pytest.mark.asyncio
    async def test_fetch_page_success(self) -> None:
        from app.scrapers.base import HttpScraper

        class TestScraper(HttpScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 100.0
            max_retries = 1

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        mock_response = MockSelector(status=200, body="<html>OK</html>" + "x" * 1000)

        with (
            patch("app.scrapers.base._get_proxy_rotator"),
            patch("app.scrapers.base.AsyncFetcher") as mock_fetcher,
        ):
            mock_fetcher.get = AsyncMock(return_value=mock_response)
            scraper = TestScraper()
            result = await scraper.fetch_page("https://test.com/page")

        assert result.status == 200

    @pytest.mark.asyncio
    async def test_fetch_page_retries_on_block(self) -> None:
        from app.scrapers.base import HttpScraper

        class TestScraper(HttpScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 100.0
            max_retries = 2

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        blocked = MockSelector(status=403, body=BLOCKED_RESPONSE_403)
        success = MockSelector(status=200, body="<html>OK</html>" + "x" * 1000)

        with (
            patch("app.scrapers.base._get_proxy_rotator"),
            patch("app.scrapers.base.AsyncFetcher") as mock_fetcher,
            patch("app.scrapers.antidetect.HumanBehavior.random_delay", new_callable=AsyncMock),
        ):
            # First call blocked, second succeeds
            mock_fetcher.get = AsyncMock(side_effect=[blocked, success])
            scraper = TestScraper()
            result = await scraper.fetch_page("https://test.com/page")

        assert result.status == 200
        assert mock_fetcher.get.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_page_raises_after_all_retries(self) -> None:
        from app.scrapers.base import HttpScraper, ScraperError

        class TestScraper(HttpScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 100.0
            max_retries = 2

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        blocked = MockSelector(status=403, body=BLOCKED_RESPONSE_403)

        with (
            patch("app.scrapers.base._get_proxy_rotator"),
            patch("app.scrapers.base.AsyncFetcher") as mock_fetcher,
            patch("app.scrapers.antidetect.HumanBehavior.random_delay", new_callable=AsyncMock),
        ):
            mock_fetcher.get = AsyncMock(return_value=blocked)
            scraper = TestScraper()

            with pytest.raises(ScraperError):
                await scraper.fetch_page("https://test.com/page")

    @pytest.mark.asyncio
    async def test_fetch_json_success(self) -> None:
        import json

        from app.scrapers.base import HttpScraper

        class TestScraper(HttpScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 100.0
            max_retries = 1

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        mock_response = MockSelector(
            status=200,
            body=json.dumps(WB_SEARCH_JSON),
        )

        with (
            patch("app.scrapers.base._get_proxy_rotator"),
            patch("app.scrapers.base.AsyncFetcher") as mock_fetcher,
        ):
            mock_fetcher.get = AsyncMock(return_value=mock_response)
            scraper = TestScraper()
            result = await scraper.fetch_json(
                "https://api.test.com/search",
                params={"query": "iphone"},
            )

        assert "data" in result
        assert len(result["data"]["products"]) == 2


# ---------------------------------------------------------------------------
# DynamicScraper with mocked StealthyFetcher
# ---------------------------------------------------------------------------


class TestDynamicScraper:
    """Tests for DynamicScraper.fetch_page."""

    @pytest.mark.asyncio
    async def test_fetch_page_passes_page_action(self) -> None:
        """Verify that page_action (scroll simulation) is passed to fetcher."""
        from app.scrapers.base import DynamicScraper

        class TestScraper(DynamicScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 100.0
            max_retries = 1

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        mock_response = MockSelector(status=200, body="<html>OK</html>" + "x" * 1000)

        with (
            patch("app.scrapers.base._get_proxy_rotator"),
            patch("app.scrapers.base.StealthyFetcher") as mock_fetcher,
        ):
            mock_fetcher.async_fetch = AsyncMock(return_value=mock_response)
            mock_fetcher.adaptive = True
            scraper = TestScraper()
            await scraper.fetch_page("https://test.com/page")

        # Verify page_action was included in the call
        call_kwargs = mock_fetcher.async_fetch.call_args
        assert "page_action" in call_kwargs.kwargs or (len(call_kwargs.args) > 1)

    @pytest.mark.asyncio
    async def test_fetch_page_detects_captcha(self) -> None:
        from app.scrapers.base import DynamicScraper, ScraperError

        class TestScraper(DynamicScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 100.0
            max_retries = 1

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        captcha_page = MockSelector(status=200, body=CAPTCHA_RESPONSE)

        with (
            patch("app.scrapers.base._get_proxy_rotator"),
            patch("app.scrapers.base.StealthyFetcher") as mock_fetcher,
            patch("app.scrapers.antidetect.HumanBehavior.random_delay", new_callable=AsyncMock),
        ):
            mock_fetcher.async_fetch = AsyncMock(return_value=captcha_page)
            mock_fetcher.adaptive = True
            scraper = TestScraper()

            with pytest.raises(ScraperError):
                await scraper.fetch_page("https://test.com/page")

    @pytest.mark.asyncio
    async def test_fetch_page_uses_proxy(self) -> None:
        """Verify proxy is passed to StealthyFetcher."""
        from app.scrapers.base import DynamicScraper

        class TestScraper(DynamicScraper):
            marketplace_name = "test"
            base_url = "https://test.com"
            rate_limit = 100.0
            max_retries = 1

            async def search(self, query, *, page=1):
                return []

            async def get_product(self, product_id):
                return None

        mock_response = MockSelector(status=200, body="<html>OK</html>" + "x" * 1000)

        mock_rotator = MagicMock()
        mock_proxy = MagicMock()
        mock_proxy.url = "http://proxy:8080"
        mock_rotator.get_next = AsyncMock(return_value=mock_proxy)
        mock_rotator._proxies = [mock_proxy]

        with (
            patch("app.scrapers.base._get_proxy_rotator", return_value=mock_rotator),
            patch("app.scrapers.base.StealthyFetcher") as mock_fetcher,
        ):
            mock_fetcher.async_fetch = AsyncMock(return_value=mock_response)
            mock_fetcher.adaptive = True
            scraper = TestScraper()
            await scraper.fetch_page("https://test.com/page")

        # Check that proxy was passed
        call_kwargs = mock_fetcher.async_fetch.call_args.kwargs
        assert call_kwargs.get("proxy") == "http://proxy:8080"
