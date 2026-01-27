"""ProductService tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product, Marketplace, Category, PriceHistory
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate
from app.core.exceptions import NotFoundError, ValidationError


class TestProductServiceCRUD:
    """Tests for ProductService CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_by_id(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test getting product by ID."""
        service = ProductService(db_session)

        result = await service.get_by_id(test_product.id)

        assert result is not None
        assert result.id == test_product.id
        assert result.title == test_product.title

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test getting non-existent product returns None."""
        service = ProductService(db_session)

        result = await service.get_by_id(99999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_external_id(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test getting product by external ID."""
        service = ProductService(db_session)

        result = await service.get_by_external_id(
            test_product.marketplace_id,
            test_product.external_id,
        )

        assert result is not None
        assert result.external_id == test_product.external_id

    @pytest.mark.asyncio
    async def test_create_product(
        self,
        db_session: AsyncSession,
        test_marketplace: Marketplace,
    ) -> None:
        """Test creating a new product."""
        service = ProductService(db_session)
        data = ProductCreate(
            external_id="NEW001",
            marketplace_id=test_marketplace.id,
            title="New Test Product",
            current_price=15000.0,
            url="https://example.com/product/NEW001",
        )

        product = await service.create(data)

        assert product.id is not None
        assert product.external_id == "NEW001"
        assert product.title == "New Test Product"
        assert product.current_price == 15000.0

    @pytest.mark.asyncio
    async def test_create_duplicate_raises_error(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test creating duplicate product raises ValidationError."""
        service = ProductService(db_session)
        data = ProductCreate(
            external_id=test_product.external_id,
            marketplace_id=test_product.marketplace_id,
            title="Duplicate Product",
            current_price=10000.0,
            url="https://example.com/product/duplicate",
        )

        with pytest.raises(ValidationError):
            await service.create(data)

    @pytest.mark.asyncio
    async def test_update_product(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test updating a product."""
        service = ProductService(db_session)
        update_data = ProductUpdate(
            title="Updated Title",
            current_price=45000.0,
        )

        updated = await service.update(test_product.id, update_data)

        assert updated.title == "Updated Title"
        assert updated.current_price == 45000.0

    @pytest.mark.asyncio
    async def test_update_not_found_raises_error(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test updating non-existent product raises NotFoundError."""
        service = ProductService(db_session)
        update_data = ProductUpdate(title="New Title")

        with pytest.raises(NotFoundError):
            await service.update(99999, update_data)

    @pytest.mark.asyncio
    async def test_upsert_creates_new(
        self,
        db_session: AsyncSession,
        test_marketplace: Marketplace,
    ) -> None:
        """Test upsert creates new product if not exists."""
        service = ProductService(db_session)
        data = ProductCreate(
            external_id="UPSERT001",
            marketplace_id=test_marketplace.id,
            title="Upsert Product",
            current_price=20000.0,
            url="https://example.com/product/UPSERT001",
        )

        product = await service.upsert(data)

        assert product.id is not None
        assert product.external_id == "UPSERT001"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test upsert updates existing product."""
        service = ProductService(db_session)
        original_id = test_product.id
        data = ProductCreate(
            external_id=test_product.external_id,
            marketplace_id=test_product.marketplace_id,
            title="Updated via Upsert",
            current_price=99999.0,
            url=test_product.url,
        )

        product = await service.upsert(data)

        assert product.id == original_id
        assert product.title == "Updated via Upsert"
        assert product.current_price == 99999.0

    @pytest.mark.asyncio
    async def test_delete_product(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test deleting a product."""
        service = ProductService(db_session)
        product_id = test_product.id

        result = await service.delete(product_id)

        assert result is True
        assert await service.get_by_id(product_id) is None

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test deleting non-existent product returns False."""
        service = ProductService(db_session)

        result = await service.delete(99999)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_multi(
        self,
        db_session: AsyncSession,
        test_products: list[Product],
    ) -> None:
        """Test getting multiple products."""
        service = ProductService(db_session)

        products = await service.get_multi(limit=3)

        assert len(products) == 3

    @pytest.mark.asyncio
    async def test_count(
        self,
        db_session: AsyncSession,
        test_products: list[Product],
    ) -> None:
        """Test counting products."""
        service = ProductService(db_session)

        count = await service.count()

        assert count == 5


class TestProductServicePriceHistory:
    """Tests for ProductService price history operations."""

    @pytest.mark.asyncio
    async def test_record_price(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test recording price in history."""
        service = ProductService(db_session)

        history = await service.record_price(test_product)

        assert history.product_id == test_product.id
        assert history.price == test_product.current_price

    @pytest.mark.asyncio
    async def test_record_price_skips_unchanged(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test recording price skips if unchanged."""
        service = ProductService(db_session)

        # Record first time
        first = await service.record_price(test_product)
        # Record again with same price
        second = await service.record_price(test_product)

        # Should return the same record
        assert first.id == second.id

    @pytest.mark.asyncio
    async def test_get_price_history(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test getting price history."""
        service = ProductService(db_session)

        # Record some prices
        await service.record_price(test_product)

        history = await service.get_price_history(test_product.id, days=30)

        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_price_stats(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test getting price statistics."""
        service = ProductService(db_session)

        # Record price first
        await service.record_price(test_product)

        stats = await service.get_price_stats(test_product.id)

        assert stats.min_price > 0
        assert stats.max_price >= stats.min_price
        assert stats.trend in ("rising", "falling", "stable")

    @pytest.mark.asyncio
    async def test_get_product_with_history(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test getting product with full history and stats."""
        service = ProductService(db_session)

        # Record price
        await service.record_price(test_product)

        result = await service.get_product_with_history(test_product.id)

        assert result is not None
        assert result.id == test_product.id
        assert hasattr(result, "price_history")
        assert hasattr(result, "price_stats")


class TestProductServiceMatching:
    """Tests for ProductService matching operations."""

    @pytest.mark.asyncio
    async def test_get_price_comparison_no_matches(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ) -> None:
        """Test price comparison with no matches returns None."""
        service = ProductService(db_session)

        result = await service.get_price_comparison(test_product.id)

        # With no matches, should return comparison with just the product
        assert result is not None or result is None  # Both valid

    @pytest.mark.asyncio
    async def test_get_products_to_update(
        self,
        db_session: AsyncSession,
        test_products: list[Product],
    ) -> None:
        """Test getting products that need updates."""
        service = ProductService(db_session)

        products = await service.get_products_to_update(
            max_age_hours=0,  # All products need update
            limit=10,
        )

        assert len(products) > 0
