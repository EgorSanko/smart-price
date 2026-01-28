"""Tests for base scraper classes."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.scrapers.base import (
    BaseScraper,
    BlockedError,
    PlaywrightScraper,
    RateLimitError,
    ScraperError,
)


class ConcreteScraper(BaseScraper):
    """Concrete implementation for testing."""

    marketplace_name = "test"
    base_url = "https://test.example.com"
    rate_limit = 10.0  # Fast for tests

    async def search(self, query: str, page: int = 1, **kwargs):
        return []

    async def get_product(self, product_id: str):
        return None

    async def get_category(self, category_url: str, max_pages: int = 10):
        yield  # Empty generator


class TestBaseScraper:
    """Tests for BaseScraper class."""

    @pytest.fixture
    def scraper(self) -> ConcreteScraper:
        """Create test scraper instance."""
        return ConcreteScraper()

    def test_init_without_proxy(self, scraper: ConcreteScraper) -> None:
        """Should initialize without proxy."""
        assert scraper._proxy_url is None
        assert scraper._client is None
        assert scraper.marketplace_name == "test"

    def test_init_with_proxy(self) -> None:
        """Should initialize with proxy."""
        proxy = "http://proxy:8080"
        scraper = ConcreteScraper(proxy_url=proxy)
        assert scraper._proxy_url == proxy

    def test_get_headers(self, scraper: ConcreteScraper) -> None:
        """Should return proper headers."""
        headers = scraper._get_headers()

        assert "User-Agent" in headers
        assert "Mozilla" in headers["User-Agent"]
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "ru-RU" in headers["Accept-Language"]

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self, scraper: ConcreteScraper) -> None:
        """Should create HTTP client on first call."""
        assert scraper._client is None

        client = await scraper._get_client()

        assert client is not None
        assert scraper._client is client
        await scraper.close()

    @pytest.mark.asyncio
    async def test_get_client_reuses_client(self, scraper: ConcreteScraper) -> None:
        """Should reuse existing client."""
        client1 = await scraper._get_client()
        client2 = await scraper._get_client()

        assert client1 is client2
        await scraper.close()

    @pytest.mark.asyncio
    async def test_rate_limit_wait(self, scraper: ConcreteScraper) -> None:
        """Should wait between requests."""
        scraper.rate_limit = 2.0  # 2 requests per second

        start = asyncio.get_event_loop().time()
        await scraper._rate_limit_wait()
        await scraper._rate_limit_wait()
        elapsed = asyncio.get_event_loop().time() - start

        # Should wait at least 0.5 seconds between calls
        assert elapsed >= 0.4  # Some tolerance

    @pytest.mark.asyncio
    async def test_fetch_success(self, scraper: ConcreteScraper) -> None:
        """Should fetch HTML successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await scraper.fetch("https://example.com")

            assert result == "<html>test</html>"
            mock_get.assert_called_once()

        await scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_rate_limit_error(self, scraper: ConcreteScraper) -> None:
        """Should raise RateLimitError on 429."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            with pytest.raises(RateLimitError):
                await scraper.fetch("https://example.com")

        await scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_blocked_error(self, scraper: ConcreteScraper) -> None:
        """Should raise BlockedError on 403."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            with pytest.raises(BlockedError):
                await scraper.fetch("https://example.com")

        await scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_json(self, scraper: ConcreteScraper) -> None:
        """Should fetch and parse JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await scraper.fetch_json("https://api.example.com/data")

            assert result == {"key": "value"}

        await scraper.close()

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as async context manager."""
        async with ConcreteScraper() as scraper:
            assert isinstance(scraper, ConcreteScraper)

        # Client should be closed
        assert scraper._client is None

    @pytest.mark.asyncio
    async def test_close(self, scraper: ConcreteScraper) -> None:
        """Should close HTTP client."""
        await scraper._get_client()
        assert scraper._client is not None

        await scraper.close()
        assert scraper._client is None


class TestScraperErrors:
    """Tests for scraper exception hierarchy."""

    def test_scraper_error_is_base(self) -> None:
        """ScraperError should be base exception."""
        assert issubclass(RateLimitError, ScraperError)
        assert issubclass(BlockedError, ScraperError)

    def test_rate_limit_error(self) -> None:
        """RateLimitError should carry message."""
        error = RateLimitError("Too many requests")
        assert str(error) == "Too many requests"

    def test_blocked_error(self) -> None:
        """BlockedError should carry message."""
        error = BlockedError("IP blocked")
        assert str(error) == "IP blocked"


class TestPlaywrightScraper:
    """Tests for PlaywrightScraper class."""

    def test_init_headless(self) -> None:
        """Should initialize with headless mode."""

        class ConcretePlaywrightScraper(PlaywrightScraper):
            marketplace_name = "test"
            base_url = "https://test.com"

            async def search(self, query, page=1, **kwargs):
                return []

            async def get_product(self, product_id):
                return None

            async def get_category(self, category_url, max_pages=10):
                yield

        scraper = ConcretePlaywrightScraper(headless=True)
        assert scraper._headless is True

        scraper = ConcretePlaywrightScraper(headless=False)
        assert scraper._headless is False
