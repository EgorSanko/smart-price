"""Fixtures for scraper tests.

Provides:
- Mock Scrapling responses (Selector-like objects)
- Fake Ozon/WB HTML and JSON data
- ProxyRotator with test proxies
- Patched settings
"""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock Scrapling Selector
# ---------------------------------------------------------------------------


@dataclass
class MockElement:
    """Mimics a Scrapling element with text/attributes."""

    _text: str = ""
    _attributes: dict[str, str] = field(default_factory=dict)
    _children: list[MockElement] = field(default_factory=list)

    def text(self, strip: bool = True) -> str:
        return self._text.strip() if strip else self._text

    def attrib(self) -> dict[str, str]:
        return self._attributes

    def css(self, selector: str) -> list[MockElement]:
        return self._children

    def css_first(self, selector: str) -> MockElement | None:
        return self._children[0] if self._children else None


@dataclass
class MockSelector:
    """Mimics Scrapling's Selector (parsed page response).

    Usage in tests:
        page = MockSelector(status=200, body=html_content)
        assert page.status == 200
    """

    status: int = 200
    body: str = ""
    url: str = "https://example.com"
    _elements: dict[str, list[MockElement]] = field(default_factory=dict)

    def css(self, selector: str) -> list[MockElement]:
        return self._elements.get(selector, [])

    def css_first(self, selector: str) -> MockElement | None:
        elements = self._elements.get(selector, [])
        return elements[0] if elements else None

    def find_by_text(self, text: str, first: bool = True) -> MockElement | None:
        for elements in self._elements.values():
            for el in elements:
                if text.lower() in el._text.lower():
                    return el if first else el
        return None

    def re(self, pattern: str) -> list[str]:
        import re

        return re.findall(pattern, self.body)


# ---------------------------------------------------------------------------
# Fake marketplace data
# ---------------------------------------------------------------------------


OZON_SEARCH_JSON = {
    "items": [
        {
            "id": 123456,
            "mainState": [
                {
                    "atom": {
                        "type": "title",
                        "textAtom": {"text": "Apple iPhone 15 128GB Чёрный"},
                    }
                },
                {
                    "atom": {
                        "type": "price",
                        "priceAtom": {
                            "price": "79 990 ₽",
                            "originalPrice": "89 990 ₽",
                        },
                    }
                },
            ],
            "tileImage": {"url": "https://ir.ozon.ru/s3/multimedia/123.jpg"},
            "rating": 4.8,
            "reviewsCount": 1234,
        },
        {
            "id": 789012,
            "mainState": [
                {
                    "atom": {
                        "type": "title",
                        "textAtom": {"text": "Apple iPhone 15 Pro 256GB"},
                    }
                },
                {
                    "atom": {
                        "type": "price",
                        "priceAtom": {
                            "price": "109 990 ₽",
                            "originalPrice": None,
                        },
                    }
                },
            ],
            "tileImage": {"url": "https://ir.ozon.ru/s3/multimedia/789.jpg"},
            "rating": 4.9,
            "reviewsCount": 567,
        },
    ]
}


WB_SEARCH_JSON = {
    "data": {
        "products": [
            {
                "id": 111222333,
                "name": "Смартфон Apple iPhone 15 128Gb",
                "brand": "Apple",
                "brandId": 6049,
                "salePriceU": 7999000,  # kopecks → 79990.00 RUB
                "priceU": 8999000,
                "rating": 4.7,
                "feedbacks": 890,
                "colors": [{"name": "Чёрный"}],
            },
            {
                "id": 444555666,
                "name": "Чехол для iPhone 15",
                "brand": "Noname",
                "brandId": 1234,
                "salePriceU": 59900,  # 599.00 RUB
                "priceU": 99900,
                "rating": 4.2,
                "feedbacks": 45,
                "colors": [],
            },
        ]
    }
}


WB_DETAIL_JSON = {
    "data": {
        "products": [
            {
                "id": 111222333,
                "name": "Смартфон Apple iPhone 15 128Gb",
                "brand": "Apple",
                "brandId": 6049,
                "salePriceU": 7999000,
                "priceU": 8999000,
                "rating": 4.7,
                "feedbacks": 890,
                "sizes": [
                    {
                        "origName": "128Gb",
                        "stocks": [{"qty": 5, "wh": 507}],
                    }
                ],
                "colors": [{"name": "Чёрный"}],
            }
        ]
    }
}


OZON_PRODUCT_HTML = """
<html>
<head><title>Apple iPhone 15 — купить на Ozon</title></head>
<body>
<div data-widget="webProductHeading">
    <h1>Apple iPhone 15 128GB Чёрный</h1>
</div>
<div data-widget="webPrice">
    <span>79 990 ₽</span>
    <span class="original">89 990 ₽</span>
</div>
<div data-widget="webDescription">
    <p>Смартфон Apple iPhone 15 с чипом A16 Bionic</p>
</div>
<div data-widget="webReviewProductScore">
    <span>4.8</span>
    <span>1234 отзыва</span>
</div>
<div data-widget="webGallery">
    <img src="https://ir.ozon.ru/img1.jpg" />
    <img src="https://ir.ozon.ru/img2.jpg" />
</div>
<div data-widget="webCharacteristics">
    <dl>
        <dt>Бренд</dt><dd>Apple</dd>
        <dt>Память</dt><dd>128 ГБ</dd>
    </dl>
</div>
<script type="application/json" data-state="webProductHeading-123">
{"title": "Apple iPhone 15 128GB Чёрный"}
</script>
</body>
</html>
"""


BLOCKED_RESPONSE_403 = "<html><body><h1>403 Forbidden</h1></body></html>"

CAPTCHA_RESPONSE = """
<html><body>
<div class="captcha-page">
    <h1>Подтвердите, что вы не робот</h1>
    <div class="captcha-container">
        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
    </div>
</div>
</body></html>
"""

CLOUDFLARE_RESPONSE = """
<html>
<head><title>Just a moment...</title></head>
<body>
<div id="cf-browser-verification">
    <p>Checking your browser before accessing the site.</p>
    <span class="ray-id">Ray ID: abc123</span>
</div>
</body></html>
"""

EMPTY_RESPONSE = "<html><body></body></html>"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_selector_ok() -> MockSelector:
    """A successful mock page response."""
    return MockSelector(status=200, body=OZON_PRODUCT_HTML)


@pytest.fixture
def mock_selector_blocked() -> MockSelector:
    """A 403 blocked response."""
    return MockSelector(status=403, body=BLOCKED_RESPONSE_403)


@pytest.fixture
def mock_selector_captcha() -> MockSelector:
    """A captcha challenge response."""
    return MockSelector(status=200, body=CAPTCHA_RESPONSE)


@pytest.fixture
def mock_selector_cloudflare() -> MockSelector:
    """A Cloudflare challenge response."""
    return MockSelector(status=503, body=CLOUDFLARE_RESPONSE)


@pytest.fixture
def mock_selector_empty() -> MockSelector:
    """An empty/truncated response."""
    return MockSelector(status=200, body=EMPTY_RESPONSE)


@pytest.fixture
def test_proxy_urls() -> list[str]:
    """Test proxy URLs (not real)."""
    return [
        "http://user:pass@proxy1.test.com:8080",
        "http://user:pass@proxy2.test.com:8080",
        "http://user:pass@proxy3.test.com:8080",
    ]


@pytest.fixture
def mock_settings():
    """Patch settings to provide test proxy config."""
    with patch("app.scrapers.antidetect.settings") as mock:
        mock.SCRAPER_PROXY_URLS = (
            "http://user:pass@proxy1.test.com:8080," "http://user:pass@proxy2.test.com:8080"
        )
        mock.SCRAPER_PROXY_TYPE = "residential"
        yield mock


@pytest.fixture
def mock_stealthy_fetcher():
    """Patch StealthyFetcher.async_fetch to return mock data."""
    with patch("app.scrapers.base.StealthyFetcher") as mock:
        mock.async_fetch = AsyncMock()
        mock.adaptive = True
        yield mock


@pytest.fixture
def mock_async_fetcher():
    """Patch AsyncFetcher.get to return mock data."""
    with patch("app.scrapers.base.AsyncFetcher") as mock:
        mock.get = AsyncMock()
        yield mock
