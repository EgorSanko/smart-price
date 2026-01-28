"""Product indexer for automatic vectorization.

Integrates with ProductService to automatically index
products in Qdrant when they are created or updated.

Example:
    >>> indexer = ProductIndexer(embedding_service, qdrant_service)
    >>> await indexer.index_product(product)
    >>> await indexer.reindex_all(products)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.services.qdrant_service import PRODUCTS_COLLECTION

if TYPE_CHECKING:
    from app.ml.embeddings import EmbeddingService
    from app.services.qdrant_service import QdrantService

logger = structlog.get_logger()


class ProductIndexer:
    """Service for indexing products in vector database."""

    def __init__(
        self,
        embedding_service: "EmbeddingService",
        qdrant_service: "QdrantService",
    ) -> None:
        """Initialize ProductIndexer."""
        self._embeddings = embedding_service
        self._qdrant = qdrant_service
        logger.info("product_indexer_initialized")

    async def init_index(self, recreate: bool = False) -> None:
        """Initialize products collection in Qdrant."""
        await self._qdrant.init_collection(
            name=PRODUCTS_COLLECTION,
            dimension=self._embeddings.dimension,
            distance="Cosine",
            recreate=recreate,
        )
        logger.info("products_index_initialized", dimension=self._embeddings.dimension)

    async def index_product(self, product: dict[str, Any]) -> None:
        """Index single product."""
        product_id = product["id"]

        embedding = await self._embeddings.encode_product(product)

        await self._qdrant.upsert_product(
            product_id=product_id,
            embedding=embedding,
            title=product.get("title", ""),
            marketplace_id=product.get("marketplace_id", 0),
            price=product.get("current_price") or product.get("price", 0),
            brand=product.get("brand"),
            category_id=product.get("category_id"),
            is_available=product.get("is_available", True),
            url=product.get("url"),
            image_url=product.get("image_url"),
            original_price=product.get("original_price"),
            rating=product.get("rating"),
            reviews_count=product.get("reviews_count"),
        )

        logger.debug("product_indexed", product_id=product_id)

    async def index_products(
        self,
        products: list[dict[str, Any]],
        batch_size: int = 50,
    ) -> int:
        """Index multiple products."""
        total = len(products)
        indexed = 0

        for i in range(0, total, batch_size):
            batch = products[i : i + batch_size]

            embeddings = await self._embeddings.encode_batch([
                self._build_text(p) for p in batch
            ])

            ids = [p["id"] for p in batch]
            payloads = [self._build_payload(p) for p in batch]

            self._qdrant.upsert_batch(
                collection=PRODUCTS_COLLECTION,
                ids=ids,
                vectors=embeddings,
                payloads=payloads,
            )

            indexed += len(batch)
            logger.info("batch_indexed", indexed=indexed, total=total)

        logger.info("indexing_complete", total=indexed)
        return indexed

    async def delete_product(self, product_id: int) -> None:
        """Remove product from index."""
        await self._qdrant.delete(PRODUCTS_COLLECTION, [product_id])
        logger.debug("product_removed_from_index", product_id=product_id)

    async def reindex_all(
        self,
        products: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """Reindex all products (recreate collection)."""
        await self.init_index(recreate=True)
        return await self.index_products(products, batch_size)

    def _build_text(self, product: dict[str, Any]) -> str:
        """Build text for embedding from product."""
        parts = [product.get("title", "")]

        if brand := product.get("brand"):
            parts.append(f"бренд: {brand}")

        if desc := product.get("description"):
            parts.append(desc[:500])

        return " ".join(parts)

    def _build_payload(self, product: dict[str, Any]) -> dict[str, Any]:
        """Build Qdrant payload from product."""
        return {
            "title": product.get("title"),
            "brand": product.get("brand"),
            "marketplace_id": product.get("marketplace_id"),
            "price": product.get("current_price") or product.get("price"),
            "original_price": product.get("original_price"),
            "category_id": product.get("category_id"),
            "is_available": product.get("is_available", True),
            "url": product.get("url"),
            "image_url": product.get("image_url"),
            "rating": product.get("rating"),
            "reviews_count": product.get("reviews_count"),
        }


_product_indexer: ProductIndexer | None = None


def get_product_indexer(
    embedding_service: "EmbeddingService",
    qdrant_service: "QdrantService",
) -> ProductIndexer:
    """Get singleton ProductIndexer."""
    global _product_indexer
    if _product_indexer is None:
        _product_indexer = ProductIndexer(embedding_service, qdrant_service)
    return _product_indexer
