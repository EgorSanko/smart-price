"""Pytest configuration and fixtures for scraper tests."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_ozon_search_html() -> str:
    """Sample Ozon search results HTML."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Search Results</title></head>
    <body>
        <div data-widget="searchResultsV2">
            <div class="tile-root">
                <a href="/product/test-product-123456/">
                    <img src="https://cdn.ozon.ru/s3/multimedia/image.jpg">
                </a>
                <span class="tsBody500Medium">Test Product Title</span>
                <span class="c3015-a1">1 234 ₽</span>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_ozon_product_html() -> str:
    """Sample Ozon product page HTML."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Product Page</title></head>
    <body>
        <h1 data-widget="webProductHeading">Test Product</h1>
        <div data-widget="webPrice">
            <span>999 ₽</span>
            <del>1 499 ₽</del>
        </div>
        <div data-widget="webBrand">
            <a href="/brand/test/">Test Brand</a>
        </div>
        <div data-widget="webSingleProductScore">
            <span>4.5</span>
        </div>
        <div data-widget="webReviewProductScore">
            <span>123 отзыва</span>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_wb_api_response() -> dict:
    """Sample Wildberries API response."""
    return {
        "data": {
            "products": [
                {
                    "id": 123456789,
                    "name": "Test Product",
                    "brand": "Test Brand",
                    "sizes": [
                        {
                            "price": {"product": 99900, "basic": 149900},
                            "stocks": [{"qty": 10, "wh": 507}],
                        }
                    ],
                    "reviewRating": 4.5,
                    "feedbacks": 100,
                    "supplierId": 12345,
                    "supplier": "Test Seller",
                    "subjectId": 515,
                    "subjectParentName": "Электроника",
                    "colors": [{"name": "Черный"}],
                },
                {
                    "id": 987654321,
                    "name": "Another Product",
                    "brand": "Another Brand",
                    "sizes": [
                        {
                            "price": {"product": 199900},
                            "stocks": [],  # Out of stock
                        }
                    ],
                    "reviewRating": 4.0,
                    "feedbacks": 50,
                },
            ]
        }
    }
