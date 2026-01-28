"""Tests for scraper utilities."""

from __future__ import annotations

import asyncio

import pytest

from app.scrapers.utils import (
    ProxyRotator,
    RateLimiter,
    build_url,
    clean_text,
    extract_product_id,
    format_price,
    get_random_headers,
    get_random_user_agent,
    normalize_url,
    parse_price,
)


class TestUserAgentRotation:
    """Tests for User-Agent utilities."""

    def test_get_random_user_agent_desktop(self) -> None:
        """Should return desktop User-Agent."""
        ua = get_random_user_agent(mobile=False)

        assert "Mozilla" in ua
        assert "Mobile" not in ua or "Windows" in ua

    def test_get_random_user_agent_mobile(self) -> None:
        """Should return mobile User-Agent."""
        ua = get_random_user_agent(mobile=True)

        assert "Mozilla" in ua
        assert "Mobile" in ua or "iPhone" in ua or "Android" in ua

    def test_get_random_user_agent_randomness(self) -> None:
        """Should return different User-Agents."""
        agents = {get_random_user_agent() for _ in range(20)}

        # Should get at least 2 different agents in 20 tries
        assert len(agents) >= 2

    def test_get_random_headers(self) -> None:
        """Should return complete headers dict."""
        headers = get_random_headers()

        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "ru" in headers["Accept-Language"]

    def test_get_random_headers_with_referer(self) -> None:
        """Should include referer when provided."""
        headers = get_random_headers(referer="https://example.com")

        assert headers["Referer"] == "https://example.com"
        assert headers["Sec-Fetch-Site"] == "same-origin"


class TestPriceParsing:
    """Tests for price parsing utilities."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("1 234 ₽", 1234.0),
            ("999₽", 999.0),
            ("1,234.56", 1234.56),
            ("1.234,56", 1234.56),
            ("от 999 ₽", 999.0),
            ("до 5000", 5000.0),
            ("$99.99", 99.99),
            ("12,99", 12.99),
            ("1 000 000", 1000000.0),
            ("", None),
            (None, None),
            ("бесплатно", None),
        ],
    )
    def test_parse_price(self, input_str: str | None, expected: float | None) -> None:
        """Should parse various price formats."""
        result = parse_price(input_str)
        assert result == expected

    def test_format_price(self) -> None:
        """Should format price correctly."""
        assert format_price(1234.0) == "1 234 ₽"
        assert format_price(999.0, "$") == "999 $"
        assert format_price(1000000.0) == "1 000 000 ₽"


class TestTextCleaning:
    """Tests for text cleaning utilities."""

    def test_clean_text_whitespace(self) -> None:
        """Should normalize whitespace."""
        assert clean_text("hello   world") == "hello world"
        assert clean_text("  spaced  ") == "spaced"
        assert clean_text("line\n\nbreak") == "line break"

    def test_clean_text_html_entities(self) -> None:
        """Should decode HTML entities."""
        assert clean_text("Tom &amp; Jerry") == "Tom & Jerry"
        assert clean_text("5 &gt; 3") == "5 > 3"
        assert clean_text("&quot;quoted&quot;") == '"quoted"'

    def test_clean_text_quotes(self) -> None:
        """Should normalize quotes."""
        assert clean_text('"smart quotes"') == '"smart quotes"'
        assert clean_text("'apostrophe'") == "'apostrophe'"

    def test_clean_text_empty(self) -> None:
        """Should handle empty input."""
        assert clean_text("") == ""
        assert clean_text(None) == ""


class TestProductIdExtraction:
    """Tests for product ID extraction."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://www.ozon.ru/product/smartfon-123456/", "123456"),
            ("https://www.ozon.ru/product/123456", "123456"),
            ("https://www.wildberries.ru/catalog/123456/detail.aspx", "123456"),
            ("https://market.yandex.ru/product--iphone/123456", "123456"),
            ("https://example.com?id=123456", "123456"),
            ("https://example.com?sku=789", "789"),
            ("https://example.com/no-id-here", None),
        ],
    )
    def test_extract_product_id(self, url: str, expected: str | None) -> None:
        """Should extract product ID from various URL formats."""
        assert extract_product_id(url) == expected


class TestProxyRotator:
    """Tests for proxy rotation."""

    def test_rotator_empty(self) -> None:
        """Should handle empty proxy list."""
        rotator = ProxyRotator([])
        assert rotator.get_next() is None

    def test_rotator_single_proxy(self) -> None:
        """Should return single proxy repeatedly."""
        rotator = ProxyRotator(["http://proxy:8080"])

        assert rotator.get_next() == "http://proxy:8080"
        assert rotator.get_next() == "http://proxy:8080"

    def test_rotator_multiple_proxies(self) -> None:
        """Should rotate through proxies."""
        proxies = ["http://p1:8080", "http://p2:8080", "http://p3:8080"]
        rotator = ProxyRotator(proxies)

        # Get all proxies
        results = [rotator.get_next() for _ in range(6)]

        # Should have used all proxies
        assert set(results) == set(proxies)

    def test_rotator_mark_failed(self) -> None:
        """Should skip failed proxies."""
        proxies = ["http://p1:8080", "http://p2:8080"]
        rotator = ProxyRotator(proxies)

        rotator.mark_failed("http://p1:8080")

        # Should only return p2
        assert rotator.get_next() == "http://p2:8080"
        assert rotator.get_next() == "http://p2:8080"
        assert rotator.available_count == 1

    def test_rotator_reset_on_all_failed(self) -> None:
        """Should reset when all proxies have failed."""
        proxies = ["http://p1:8080", "http://p2:8080"]
        rotator = ProxyRotator(proxies)

        rotator.mark_failed("http://p1:8080")
        rotator.mark_failed("http://p2:8080")

        # Should reset and return a proxy
        result = rotator.get_next()
        assert result in proxies


class TestRateLimiter:
    """Tests for rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self) -> None:
        """Should limit rate of operations."""
        limiter = RateLimiter(rate=10.0, burst=1)  # 10/sec

        start = asyncio.get_event_loop().time()

        async with limiter:
            pass
        async with limiter:
            pass

        elapsed = asyncio.get_event_loop().time() - start

        # Should take at least 0.1 seconds (1/rate)
        assert elapsed >= 0.08  # Some tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_burst(self) -> None:
        """Should allow burst of operations."""
        limiter = RateLimiter(rate=1.0, burst=3)

        start = asyncio.get_event_loop().time()

        # First 3 should be instant (burst)
        for _ in range(3):
            async with limiter:
                pass

        elapsed = asyncio.get_event_loop().time() - start

        # Burst should be fast
        assert elapsed < 0.5


class TestUrlUtilities:
    """Tests for URL utilities."""

    def test_normalize_url_removes_tracking(self) -> None:
        """Should remove tracking parameters."""
        url = "https://example.com/product?id=123&utm_source=google&ref=abc"
        result = normalize_url(url)

        assert "id=123" in result
        assert "utm_source" not in result
        assert "ref" not in result

    def test_normalize_url_preserves_important_params(self) -> None:
        """Should preserve non-tracking parameters."""
        url = "https://example.com/search?q=test&page=2"
        result = normalize_url(url)

        assert "q=test" in result
        assert "page=2" in result

    def test_build_url_simple(self) -> None:
        """Should build simple URL."""
        result = build_url("https://example.com", "/api/products")
        assert result == "https://example.com/api/products"

    def test_build_url_with_params(self) -> None:
        """Should build URL with query params."""
        result = build_url(
            "https://example.com",
            "/search",
            {"q": "test", "page": 1, "empty": None},
        )

        assert "q=test" in result
        assert "page=1" in result
        assert "empty" not in result
