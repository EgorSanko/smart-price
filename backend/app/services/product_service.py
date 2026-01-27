"""Product service - business logic for product operations."""

from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import Category, Marketplace, PriceHistory, Product
from app.schemas.product import (
    PricePoint,
    PriceStats,
    ProductCreate,
    ProductUpdate,
    ProductWithPriceHistory,
)


class ProductService:
    """Service for product CRUD operations and business logic.
    
    Attributes:
        session: Async database session.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
    
    async def get_by_id(
        self,
        product_id: int,
        *,
        load_relations: bool = True,
    ) -> Product | None:
        """Get product by ID.
        
        Args:
            product_id: Product primary key.
            load_relations: Whether to eagerly load marketplace and category.
            
        Returns:
            Product instance or None if not found.
        """
        stmt = select(Product).where(Product.id == product_id)
        
        if load_relations:
            stmt = stmt.options(
                joinedload(Product.marketplace),
                joinedload(Product.category),
            )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_external_id(
        self,
        marketplace_id: int,
        external_id: str,
    ) -> Product | None:
        """Get product by marketplace and external ID.
        
        Args:
            marketplace_id: Marketplace foreign key.
            external_id: Product ID on the marketplace.
            
        Returns:
            Product instance or None if not found.
        """
        stmt = select(Product).where(
            Product.marketplace_id == marketplace_id,
            Product.external_id == external_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_products(
        self,
        *,
        marketplace_id: int | None = None,
        category_id: int | None = None,
        is_available: bool | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        brand: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[Sequence[Product], int]:
        """List products with filtering and pagination.
        
        Args:
            marketplace_id: Filter by marketplace.
            category_id: Filter by category.
            is_available: Filter by availability.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            brand: Filter by brand name.
            page: Page number (1-indexed).
            per_page: Items per page.
            
        Returns:
            Tuple of (products list, total count).
        """
        # Base query
        stmt = select(Product).options(
            joinedload(Product.marketplace),
            joinedload(Product.category),
        )
        count_stmt = select(func.count(Product.id))
        
        # Apply filters
        if marketplace_id is not None:
            stmt = stmt.where(Product.marketplace_id == marketplace_id)
            count_stmt = count_stmt.where(Product.marketplace_id == marketplace_id)
        
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
            count_stmt = count_stmt.where(Product.category_id == category_id)
        
        if is_available is not None:
            stmt = stmt.where(Product.is_available == is_available)
            count_stmt = count_stmt.where(Product.is_available == is_available)
        
        if min_price is not None:
            stmt = stmt.where(Product.current_price >= min_price)
            count_stmt = count_stmt.where(Product.current_price >= min_price)
        
        if max_price is not None:
            stmt = stmt.where(Product.current_price <= max_price)
            count_stmt = count_stmt.where(Product.current_price <= max_price)
        
        if brand:
            stmt = stmt.where(Product.brand.ilike(f"%{brand}%"))
            count_stmt = count_stmt.where(Product.brand.ilike(f"%{brand}%"))
        
        # Get total count
        total = await self.session.scalar(count_stmt) or 0
        
        # Apply pagination and ordering
        stmt = (
            stmt
            .order_by(Product.updated_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        
        result = await self.session.execute(stmt)
        products = result.scalars().unique().all()
        
        return products, total
    
    async def create(self, data: ProductCreate) -> Product:
        """Create a new product.
        
        Args:
            data: Product creation data.
            
        Returns:
            Created Product instance.
            
        Raises:
            ValidationError: If marketplace doesn't exist.
        """
        # Verify marketplace exists
        marketplace = await self.session.get(Marketplace, data.marketplace_id)
        if not marketplace:
            raise ValidationError(
                field="marketplace_id",
                reason=f"Marketplace {data.marketplace_id} not found",
            )
        
        # Verify category exists if provided
        if data.category_id:
            category = await self.session.get(Category, data.category_id)
            if not category:
                raise ValidationError(
                    field="category_id",
                    reason=f"Category {data.category_id} not found",
                )
        
        # Create product
        product = Product(
            external_id=data.external_id,
            marketplace_id=data.marketplace_id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            brand=data.brand,
            current_price=data.current_price,
            original_price=data.original_price,
            currency=data.currency,
            url=str(data.url),
            image_url=str(data.image_url) if data.image_url else None,
            images=[str(img) for img in data.images] if data.images else None,
            rating=data.rating,
            reviews_count=data.reviews_count,
            specs=data.specs,
            is_available=data.is_available,
            seller_name=data.seller_name,
            seller_rating=data.seller_rating,
            last_scraped_at=datetime.utcnow(),
        )
        
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        
        # Record initial price
        await self._record_price(product)
        
        return product
    
    async def update(
        self,
        product_id: int,
        data: ProductUpdate,
    ) -> Product:
        """Update an existing product.
        
        Args:
            product_id: Product ID to update.
            data: Update data (partial).
            
        Returns:
            Updated Product instance.
            
        Raises:
            NotFoundError: If product doesn't exist.
        """
        product = await self.get_by_id(product_id, load_relations=False)
        if not product:
            raise NotFoundError(resource="Product", id=product_id)
        
        # Track if price changed
        old_price = product.current_price
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "image_url" and value:
                value = str(value)
            setattr(product, field, value)
        
        product.last_scraped_at = datetime.utcnow()
        
        await self.session.flush()
        
        # Record price if changed
        if data.current_price and data.current_price != old_price:
            await self._record_price(product)
        
        await self.session.refresh(product)
        return product
    
    async def upsert(self, data: ProductCreate) -> Product:
        """Create or update product by marketplace + external_id.
        
        Args:
            data: Product data.
            
        Returns:
            Created or updated Product instance.
        """
        existing = await self.get_by_external_id(
            data.marketplace_id,
            data.external_id,
        )
        
        if existing:
            update_data = ProductUpdate(
                title=data.title,
                description=data.description,
                brand=data.brand,
                current_price=data.current_price,
                original_price=data.original_price,
                image_url=data.image_url,
                rating=data.rating,
                reviews_count=data.reviews_count,
                is_available=data.is_available,
                seller_name=data.seller_name,
                seller_rating=data.seller_rating,
            )
            return await self.update(existing.id, update_data)
        
        return await self.create(data)
    
    async def delete(self, product_id: int) -> None:
        """Delete a product.
        
        Args:
            product_id: Product ID to delete.
            
        Raises:
            NotFoundError: If product doesn't exist.
        """
        product = await self.get_by_id(product_id, load_relations=False)
        if not product:
            raise NotFoundError(resource="Product", id=product_id)
        
        await self.session.delete(product)
        await self.session.flush()
    
    async def get_with_price_history(
        self,
        product_id: int,
        days: int = 30,
    ) -> ProductWithPriceHistory | None:
        """Get product with price history and statistics.
        
        Args:
            product_id: Product ID.
            days: Number of days of history to include.
            
        Returns:
            Product with price history or None if not found.
        """
        product = await self.get_by_id(product_id)
        if not product:
            return None
        
        # Get price history
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .where(PriceHistory.recorded_at >= since)
            .order_by(PriceHistory.recorded_at.asc())
        )
        result = await self.session.execute(stmt)
        history = result.scalars().all()
        
        # Calculate statistics
        price_stats = await self._calculate_price_stats(product, history)
        
        # Build response
        price_points = [
            PricePoint(
                price=h.price,
                original_price=h.original_price,
                recorded_at=h.recorded_at,
            )
            for h in history
        ]
        
        return ProductWithPriceHistory(
            **{
                k: v
                for k, v in product.__dict__.items()
                if not k.startswith("_")
            },
            marketplace=product.marketplace,
            category=product.category,
            price_history=price_points,
            price_stats=price_stats,
        )
    
    async def get_products_to_update(
        self,
        limit: int = 1000,
        older_than_hours: int = 1,
    ) -> Sequence[Product]:
        """Get products that need price update.
        
        Args:
            limit: Maximum number of products to return.
            older_than_hours: Only products not scraped for this many hours.
            
        Returns:
            List of products needing update.
        """
        threshold = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        stmt = (
            select(Product)
            .where(
                (Product.last_scraped_at < threshold)
                | (Product.last_scraped_at.is_(None))
            )
            .order_by(Product.last_scraped_at.asc().nullsfirst())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _record_price(self, product: Product) -> PriceHistory:
        """Record current price in history.
        
        Args:
            product: Product to record price for.
            
        Returns:
            Created PriceHistory instance.
        """
        price_record = PriceHistory(
            product_id=product.id,
            price=product.current_price,
            original_price=product.original_price,
        )
        self.session.add(price_record)
        await self.session.flush()
        return price_record
    
    async def _calculate_price_stats(
        self,
        product: Product,
        history: Sequence[PriceHistory],
    ) -> PriceStats | None:
        """Calculate price statistics from history.
        
        Args:
            product: Product instance.
            history: Price history records.
            
        Returns:
            PriceStats or None if no history.
        """
        if not history:
            return None
        
        prices = [h.price for h in history]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        # Determine trend (compare last 3 prices)
        if len(prices) >= 3:
            recent = prices[-3:]
            if recent[-1] > recent[0] * 1.02:
                trend = "rising"
            elif recent[-1] < recent[0] * 0.98:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Calculate how much above minimum
        current_vs_min = (
            ((product.current_price - min_price) / min_price * 100)
            if min_price > 0
            else 0
        )
        
        return PriceStats(
            min_price=min_price,
            max_price=max_price,
            avg_price=round(avg_price, 2),
            current_price=product.current_price,
            current_vs_min_percent=round(current_vs_min, 1),
            trend=trend,
        )
