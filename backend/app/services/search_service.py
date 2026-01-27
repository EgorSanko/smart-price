"""Search service - full-text and semantic search logic."""

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Category, Marketplace, Product
from app.schemas.product import ProductResponse
from app.schemas.search import (
    BrandFacet,
    CategoryFacet,
    MarketplaceFacet,
    PriceFacet,
    SearchFacets,
    SearchQuery,
    SearchResult,
    SearchSuggestion,
    SortOrder,
)


class SearchService:
    """Service for product search operations.
    
    Supports full-text search (PostgreSQL) and will support semantic search
    (Qdrant) in future sprints.
    
    Attributes:
        session: Async database session.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize search service.
        
        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
    
    async def search(
        self,
        query: SearchQuery,
    ) -> tuple[list[SearchResult], int, SearchFacets | None]:
        """Execute product search.
        
        Args:
            query: Search query with filters and pagination.
            
        Returns:
            Tuple of (results, total_count, facets).
        """
        # For now, implement keyword search only
        # Semantic and hybrid search will be added in Sprint 4
        
        return await self._keyword_search(query)
    
    async def _keyword_search(
        self,
        query: SearchQuery,
    ) -> tuple[list[SearchResult], int, SearchFacets | None]:
        """PostgreSQL full-text search implementation.
        
        Uses ts_vector and ts_query for Russian language search.
        
        Args:
            query: Search query parameters.
            
        Returns:
            Tuple of (results, total_count, facets).
        """
        # Build search vectors
        search_vector = func.to_tsvector("russian", Product.title)
        search_query = func.plainto_tsquery("russian", query.q)
        rank = func.ts_rank(search_vector, search_query).label("rank")
        
        # Base query with ranking
        stmt = (
            select(Product, rank)
            .where(search_vector.op("@@")(search_query))
            .options(
                joinedload(Product.marketplace),
                joinedload(Product.category),
            )
        )
        
        # Count query
        count_stmt = (
            select(func.count(Product.id))
            .where(search_vector.op("@@")(search_query))
        )
        
        # Apply filters
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, query)
        
        # Apply sorting
        stmt = self._apply_sorting(stmt, query.sort_by, rank)
        
        # Get total count
        total = await self.session.scalar(count_stmt) or 0
        
        # Apply pagination
        stmt = (
            stmt
            .offset((query.page - 1) * query.per_page)
            .limit(query.per_page)
        )
        
        # Execute query
        result = await self.session.execute(stmt)
        rows = result.unique().all()
        
        # Build results
        results = [
            SearchResult(
                product=ProductResponse.model_validate(row[0]).model_dump(),
                score=float(row[1]) if row[1] else 0.0,
                highlights=None,  # TODO: Implement highlighting
            )
            for row in rows
        ]
        
        # Get facets if we have results
        facets = None
        if total > 0:
            facets = await self._get_facets(query)
        
        return results, total, facets
    
    def _apply_filters(
        self,
        stmt,
        count_stmt,
        query: SearchQuery,
    ):
        """Apply search filters to both queries.
        
        Args:
            stmt: Main select statement.
            count_stmt: Count statement.
            query: Search query with filters.
            
        Returns:
            Tuple of (filtered_stmt, filtered_count_stmt).
        """
        if query.marketplace_ids:
            stmt = stmt.where(Product.marketplace_id.in_(query.marketplace_ids))
            count_stmt = count_stmt.where(
                Product.marketplace_id.in_(query.marketplace_ids)
            )
        
        if query.category_ids:
            stmt = stmt.where(Product.category_id.in_(query.category_ids))
            count_stmt = count_stmt.where(
                Product.category_id.in_(query.category_ids)
            )
        
        if query.min_price is not None:
            stmt = stmt.where(Product.current_price >= query.min_price)
            count_stmt = count_stmt.where(Product.current_price >= query.min_price)
        
        if query.max_price is not None:
            stmt = stmt.where(Product.current_price <= query.max_price)
            count_stmt = count_stmt.where(Product.current_price <= query.max_price)
        
        if query.in_stock_only:
            stmt = stmt.where(Product.is_available == True)  # noqa: E712
            count_stmt = count_stmt.where(Product.is_available == True)  # noqa: E712
        
        if query.brands:
            stmt = stmt.where(Product.brand.in_(query.brands))
            count_stmt = count_stmt.where(Product.brand.in_(query.brands))
        
        if query.min_rating is not None:
            stmt = stmt.where(Product.rating >= query.min_rating)
            count_stmt = count_stmt.where(Product.rating >= query.min_rating)
        
        return stmt, count_stmt
    
    def _apply_sorting(self, stmt, sort_by: SortOrder, rank):
        """Apply sorting to query.
        
        Args:
            stmt: Select statement.
            sort_by: Sort order enum.
            rank: Relevance rank expression.
            
        Returns:
            Sorted statement.
        """
        match sort_by:
            case SortOrder.RELEVANCE:
                return stmt.order_by(rank.desc())
            case SortOrder.PRICE_ASC:
                return stmt.order_by(Product.current_price.asc())
            case SortOrder.PRICE_DESC:
                return stmt.order_by(Product.current_price.desc())
            case SortOrder.RATING:
                return stmt.order_by(Product.rating.desc().nullslast())
            case SortOrder.REVIEWS:
                return stmt.order_by(Product.reviews_count.desc())
            case SortOrder.NEWEST:
                return stmt.order_by(Product.created_at.desc())
            case _:
                return stmt.order_by(rank.desc())
    
    async def _get_facets(self, query: SearchQuery) -> SearchFacets:
        """Calculate facets for search filters.
        
        Args:
            query: Search query (for applying base filter).
            
        Returns:
            SearchFacets with aggregated data.
        """
        search_vector = func.to_tsvector("russian", Product.title)
        search_query = func.plainto_tsquery("russian", query.q)
        base_filter = search_vector.op("@@")(search_query)
        
        # Price facet
        price_stmt = (
            select(
                func.min(Product.current_price).label("min_price"),
                func.max(Product.current_price).label("max_price"),
                func.avg(Product.current_price).label("avg_price"),
            )
            .where(base_filter)
        )
        price_result = await self.session.execute(price_stmt)
        price_row = price_result.one_or_none()
        
        price_facet = None
        if price_row and price_row.min_price:
            price_facet = PriceFacet(
                min_price=float(price_row.min_price),
                max_price=float(price_row.max_price),
                avg_price=round(float(price_row.avg_price), 2),
            )
        
        # Marketplace facet
        marketplace_stmt = (
            select(
                Marketplace.id,
                Marketplace.name,
                Marketplace.display_name,
                func.count(Product.id).label("count"),
            )
            .join(Product, Product.marketplace_id == Marketplace.id)
            .where(base_filter)
            .group_by(Marketplace.id)
            .order_by(text("count DESC"))
        )
        marketplace_result = await self.session.execute(marketplace_stmt)
        marketplace_facets = [
            MarketplaceFacet(
                id=row.id,
                name=row.name,
                display_name=row.display_name,
                count=row.count,
            )
            for row in marketplace_result
        ]
        
        # Category facet
        category_stmt = (
            select(
                Category.id,
                Category.name,
                Category.slug,
                func.count(Product.id).label("count"),
            )
            .join(Product, Product.category_id == Category.id)
            .where(base_filter)
            .group_by(Category.id)
            .order_by(text("count DESC"))
            .limit(20)
        )
        category_result = await self.session.execute(category_stmt)
        category_facets = [
            CategoryFacet(
                id=row.id,
                name=row.name,
                slug=row.slug,
                count=row.count,
            )
            for row in category_result
        ]
        
        # Brand facet
        brand_stmt = (
            select(
                Product.brand,
                func.count(Product.id).label("count"),
            )
            .where(base_filter)
            .where(Product.brand.isnot(None))
            .group_by(Product.brand)
            .order_by(text("count DESC"))
            .limit(20)
        )
        brand_result = await self.session.execute(brand_stmt)
        brand_facets = [
            BrandFacet(name=row.brand, count=row.count)
            for row in brand_result
            if row.brand
        ]
        
        return SearchFacets(
            price=price_facet,
            marketplaces=marketplace_facets,
            categories=category_facets,
            brands=brand_facets,
        )
    
    async def get_suggestions(
        self,
        partial_query: str,
        limit: int = 10,
    ) -> list[SearchSuggestion]:
        """Get search autocomplete suggestions.
        
        Searches across:
        - Product titles (prefix match)
        - Brand names
        - Category names
        
        Args:
            partial_query: Partial search string.
            limit: Maximum suggestions to return.
            
        Returns:
            List of search suggestions.
        """
        suggestions: list[SearchSuggestion] = []
        pattern = f"{partial_query}%"
        
        # Product title suggestions
        title_stmt = (
            select(Product.title, func.count(Product.id).label("cnt"))
            .where(Product.title.ilike(pattern))
            .group_by(Product.title)
            .order_by(text("cnt DESC"))
            .limit(limit // 2)
        )
        title_result = await self.session.execute(title_stmt)
        for row in title_result:
            suggestions.append(
                SearchSuggestion(
                    text=row.title[:100],  # Truncate long titles
                    type="query",
                    count=row.cnt,
                )
            )
        
        # Brand suggestions
        brand_stmt = (
            select(Product.brand, func.count(Product.id).label("cnt"))
            .where(Product.brand.ilike(pattern))
            .where(Product.brand.isnot(None))
            .group_by(Product.brand)
            .order_by(text("cnt DESC"))
            .limit(limit // 4)
        )
        brand_result = await self.session.execute(brand_stmt)
        for row in brand_result:
            if row.brand:
                suggestions.append(
                    SearchSuggestion(
                        text=row.brand,
                        type="brand",
                        count=row.cnt,
                    )
                )
        
        # Category suggestions
        category_stmt = (
            select(Category.name)
            .where(Category.name.ilike(pattern))
            .limit(limit // 4)
        )
        category_result = await self.session.execute(category_stmt)
        for row in category_result:
            suggestions.append(
                SearchSuggestion(
                    text=row.name,
                    type="category",
                    count=None,
                )
            )
        
        return suggestions[:limit]
