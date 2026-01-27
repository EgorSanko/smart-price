"""Product endpoint tests."""

import pytest
from httpx import AsyncClient

from app.db.models import Product, Marketplace


class TestProductEndpoints:
    """Tests for product API endpoints."""

    @pytest.mark.asyncio
    async def test_get_products_empty(self, client: AsyncClient) -> None:
        """Test get products returns empty list when no products exist."""
        response = await client.get("/api/v1/products")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_products_with_data(
        self,
        client: AsyncClient,
        test_products: list[Product],
    ) -> None:
        """Test get products returns list of products."""
        response = await client.get("/api/v1/products")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_get_products_pagination(
        self,
        client: AsyncClient,
        test_products: list[Product],
    ) -> None:
        """Test products pagination works correctly."""
        response = await client.get("/api/v1/products?page=1&per_page=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2

    @pytest.mark.asyncio
    async def test_get_product_by_id(
        self,
        client: AsyncClient,
        test_product: Product,
    ) -> None:
        """Test get single product by ID."""
        response = await client.get(f"/api/v1/products/{test_product.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["title"] == test_product.title
        assert data["current_price"] == test_product.current_price

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient) -> None:
        """Test get product returns 404 for non-existent ID."""
        response = await client.get("/api/v1/products/99999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_product_history(
        self,
        client: AsyncClient,
        test_product: Product,
    ) -> None:
        """Test get product price history."""
        response = await client.get(f"/api/v1/products/{test_product.id}/history")

        assert response.status_code == 200
        data = response.json()
        assert "price_history" in data
        assert "price_stats" in data

    @pytest.mark.asyncio
    async def test_get_product_compare(
        self,
        client: AsyncClient,
        test_product: Product,
    ) -> None:
        """Test get product price comparison."""
        response = await client.get(f"/api/v1/products/{test_product.id}/compare")

        assert response.status_code == 200
        # May return empty comparison if no matches
        data = response.json()
        assert "matches" in data or data is None


class TestProductFilters:
    """Tests for product filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_marketplace(
        self,
        client: AsyncClient,
        test_products: list[Product],
        test_marketplace: Marketplace,
    ) -> None:
        """Test filtering products by marketplace."""
        response = await client.get(
            f"/api/v1/products?marketplace_id={test_marketplace.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(
            item["marketplace_id"] == test_marketplace.id
            for item in data["items"]
        )

    @pytest.mark.asyncio
    async def test_filter_by_price_range(
        self,
        client: AsyncClient,
        test_products: list[Product],
    ) -> None:
        """Test filtering products by price range."""
        response = await client.get(
            "/api/v1/products?min_price=11000&max_price=13000"
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert 11000 <= item["current_price"] <= 13000

    @pytest.mark.asyncio
    async def test_filter_in_stock(
        self,
        client: AsyncClient,
        test_products: list[Product],
    ) -> None:
        """Test filtering products by availability."""
        response = await client.get("/api/v1/products?in_stock=true")

        assert response.status_code == 200
        data = response.json()
        assert all(item["is_available"] for item in data["items"])
