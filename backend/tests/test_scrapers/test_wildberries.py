"""Tests for Wildberries scraper."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.scrapers.wildberries import WildberriesScraper


class TestWildberriesScraper:
    """Tests for WildberriesScraper class."""

    @pytest.fixture
    def scraper(self) -> WildberriesScraper:
        """Create test scraper instance."""
        return WildberriesScraper(marketplace_id=2)

    def test_init(self, scraper: WildberriesScraper) -> None:
        """Should initialize with correct attributes."""
        assert scraper.marketplace_name == "wildberries"
        assert scraper.base_url == "https://www.wildberries.ru"
        assert scraper._marketplace_id == 2
        assert scraper.rate_limit == 2.0

    def test_get_basket_host(self) -> None:
        """Should return correct basket host for volume."""
        assert WildberriesScraper._get_basket_host(100) == "01"
        assert WildberriesScraper._get_basket_host(200) == "02"
        assert WildberriesScraper._get_basket_host(500) == "04"
        assert WildberriesScraper._get_basket_host(1000) == "05"
        assert WildberriesScraper._get_basket_host(2000) == "13"
        assert WildberriesScraper._get_basket_host(3000) == "17"

    def test_build_image_url(self, scraper: WildberriesScraper) -> None:
        """Should build correct image URL."""
        # Product ID 12345678
        # vol = 123, part = 12345, basket = "01"
        url = scraper._build_image_url(12345678, photo_number=1, size="big")

        assert "basket-01.wbbasket.ru" in url
        assert "vol123" in url
        assert "part12345" in url
        assert "12345678" in url
        assert "big/1.webp" in url

    def test_parse_api_product(self, scraper: WildberriesScraper) -> None:
        """Should parse API product data correctly."""
        api_item = {
            "id": 123456789,
            "name": "Test Product",
            "brand": "Test Brand",
            "sizes": [
                {
                    "price": {"product": 99900, "basic": 149900},
                    "stocks": [{"qty": 10}],
                }
            ],
            "reviewRating": 4.5,
            "feedbacks": 100,
            "supplierId": 12345,
            "supplier": "Test Seller",
        }

        result = scraper._parse_api_product(api_item)

        assert result["external_id"] == "123456789"
        assert result["title"] == "Test Product"
        assert result["brand"] == "Test Brand"
        assert result["price"] == 999.0  # Converted from kopecks
        assert result["original_price"] == 1499.0
        assert result["rating"] == 4.5
        assert result["reviews_count"] == 100
        assert result["is_available"] is True
        assert result["seller_name"] == "Test Seller"
        assert "wildberries.ru/catalog/123456789" in result["url"]

    def test_parse_api_product_out_of_stock(self, scraper: WildberriesScraper) -> None:
        """Should detect out of stock products."""
        api_item = {
            "id": 123456789,
            "name": "Test Product",
            "sizes": [
                {
                    "price": {"product": 99900},
                    "stocks": [],  # No stocks
                }
            ],
        }

        result = scraper._parse_api_product(api_item)

        assert result["is_available"] is False

    def test_parse_api_product_no_discount(self, scraper: WildberriesScraper) -> None:
        """Should handle products without discount."""
        api_item = {
            "id": 123456789,
            "name": "Test Product",
            "sizes": [
                {
                    "price": {"product": 99900, "basic": 99900},  # Same price
                    "stocks": [{"qty": 5}],
                }
            ],
        }

        result = scraper._parse_api_product(api_item)

        assert result["price"] == 999.0
        assert result["original_price"] is None  # No discount

    def test_create_product(self, scraper: WildberriesScraper) -> None:
        """Should create ProductCreate from parsed data."""
        data = {
            "external_id": "123",
            "title": "Test",
            "brand": "Brand",
            "price": 100.0,
            "original_price": 150.0,
            "url": "https://wb.ru/123",
            "image_url": "https://img.wb.ru/1.jpg",
            "images": [],
            "rating": 4.0,
            "reviews_count": 50,
            "is_available": True,
            "seller_name": "Seller",
        }

        product = scraper._create_product(data)

        assert product.external_id == "123"
        assert product.marketplace_id == 2
        assert product.title == "Test"
        assert product.current_price == 100.0

    @pytest.mark.asyncio
    async def test_search_success(self, scraper: WildberriesScraper) -> None:
        """Should search and return products."""
        mock_response = {
            "data": {
                "products": [
                    {
                        "id": 111,
                        "name": "Product 1",
                        "brand": "Brand A",
                        "sizes": [
                            {"price": {"product": 50000}, "stocks": [{"qty": 1}]}
                        ],
                    },
                    {
                        "id": 222,
                        "name": "Product 2",
                        "brand": "Brand B",
                        "sizes": [
                            {"price": {"product": 75000}, "stocks": [{"qty": 2}]}
                        ],
                    },
                ]
            }
        }

        with patch.object(scraper, "fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            products = await scraper.search("test query")

            assert len(products) == 2
            assert products[0].title == "Product 1"
            assert products[0].current_price == 500.0
            assert products[1].title == "Product 2"
            assert products[1].current_price == 750.0

            # Verify API call
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            assert call_args[0][0] == scraper._search_api
            assert call_args[1]["params"]["query"] == "test query"

        await scraper.close()

    @pytest.mark.asyncio
    async def test_search_empty(self, scraper: WildberriesScraper) -> None:
        """Should handle empty search results."""
        mock_response = {"data": {"products": []}}

        with patch.object(scraper, "fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            products = await scraper.search("nonexistent product xyz123")

            assert len(products) == 0

        await scraper.close()

    @pytest.mark.asyncio
    async def test_search_api_error(self, scraper: WildberriesScraper) -> None:
        """Should handle API errors gracefully."""
        with patch.object(scraper, "fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")

            products = await scraper.search("test")

            assert len(products) == 0

        await scraper.close()

    @pytest.mark.asyncio
    async def test_get_product_success(self, scraper: WildberriesScraper) -> None:
        """Should fetch single product."""
        mock_card_response = {
            "data": {
                "products": [
                    {
                        "id": 12345,
                        "name": "Test Product",
                        "brand": "Test Brand",
                        "sizes": [
                            {"price": {"product": 100000}, "stocks": [{"qty": 5}]}
                        ],
                        "reviewRating": 4.8,
                        "feedbacks": 200,
                    }
                ]
            }
        }

        mock_detail_response = {
            "description": "Product description",
            "options": [
                {"name": "Color", "value": "Black"},
                {"name": "Size", "value": "M"},
            ],
        }

        with patch.object(scraper, "fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [mock_card_response, mock_detail_response]

            product = await scraper.get_product("12345")

            assert product is not None
            assert product.title == "Test Product"
            assert product.current_price == 1000.0
            assert product.rating == 4.8

        await scraper.close()

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, scraper: WildberriesScraper) -> None:
        """Should return None for non-existent product."""
        mock_response = {"data": {"products": []}}

        with patch.object(scraper, "fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            product = await scraper.get_product("999999999")

            assert product is None

        await scraper.close()

    @pytest.mark.asyncio
    async def test_get_category(self, scraper: WildberriesScraper) -> None:
        """Should iterate over category products."""
        mock_responses = [
            {
                "data": {
                    "products": [
                        {
                            "id": 1,
                            "name": "Product 1",
                            "sizes": [
                                {"price": {"product": 10000}, "stocks": [{"qty": 1}]}
                            ],
                        }
                    ]
                }
            },
            {"data": {"products": []}},  # Empty page to stop
        ]

        with patch.object(scraper, "fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = mock_responses

            products = []
            async for product in scraper.get_category(
                "https://wb.ru/catalog?subject=123", max_pages=5
            ):
                products.append(product)

            assert len(products) == 1
            assert products[0].title == "Product 1"

        await scraper.close()

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as context manager."""
        async with WildberriesScraper() as scraper:
            assert isinstance(scraper, WildberriesScraper)

    def test_headers(self, scraper: WildberriesScraper) -> None:
        """Should have correct headers for API."""
        headers = scraper._get_headers()

        assert headers["Accept"] == "application/json"
        assert headers["Origin"] == scraper.base_url


class TestWildberriesScraperIntegration:
    """Integration tests (require network, skip by default)."""

    @pytest.mark.skip(reason="Integration test - requires network")
    @pytest.mark.asyncio
    async def test_real_search(self) -> None:
        """Test real search (manual run only)."""
        async with WildberriesScraper() as scraper:
            products = await scraper.search("iphone", page=1)

            assert len(products) > 0
            for p in products[:5]:
                print(f"{p.title}: {p.current_price} ₽")
