"""Qdrant vector database service.

Provides high-level interface for vector storage and search.

Example:
    >>> service = QdrantService()
    >>> await service.init_collection("products", dimension=1536)
    >>> await service.upsert_product(product_id=1, embedding=vec, title="iPhone")
    >>> results = await service.search_products(query_vector, limit=10)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from qdrant_client import AsyncQdrantClient, QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = structlog.get_logger()

PRODUCTS_COLLECTION = "products"


class QdrantService:
    """Service for Qdrant vector database operations."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: str | None = None,
    ) -> None:
        """Initialize Qdrant service."""
        self.host = host
        self.port = port

        self._async_client = AsyncQdrantClient(
            host=host,
            port=port,
            api_key=api_key,
        )

        self._sync_client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
        )

        logger.info("qdrant_service_initialized", host=host, port=port)

    # ==================== Collection Management ====================

    async def init_collection(
        self,
        name: str,
        dimension: int,
        distance: str = "Cosine",
        recreate: bool = False,
    ) -> bool:
        """Initialize collection if not exists."""
        try:
            collections = await self._async_client.get_collections()
            exists = any(c.name == name for c in collections.collections)

            if exists:
                if recreate:
                    await self._async_client.delete_collection(name)
                    logger.info("collection_deleted", name=name)
                else:
                    logger.info("collection_exists", name=name)
                    return False

            distance_map = {
                "Cosine": models.Distance.COSINE,
                "Euclidean": models.Distance.EUCLID,
                "Dot": models.Distance.DOT,
            }

            await self._async_client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=distance_map.get(distance, models.Distance.COSINE),
                ),
            )

            await self._create_payload_indexes(name)

            logger.info("collection_created", name=name, dimension=dimension)
            return True

        except Exception as e:
            logger.error("collection_init_failed", name=name, error=str(e))
            raise

    async def _create_payload_indexes(self, collection: str) -> None:
        """Create payload indexes for efficient filtering."""
        indexes = [
            ("marketplace_id", models.PayloadSchemaType.INTEGER),
            ("category_id", models.PayloadSchemaType.INTEGER),
            ("price", models.PayloadSchemaType.FLOAT),
            ("is_available", models.PayloadSchemaType.BOOL),
            ("brand", models.PayloadSchemaType.KEYWORD),
        ]

        for field_name, field_type in indexes:
            try:
                await self._async_client.create_payload_index(
                    collection_name=collection,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except UnexpectedResponse:
                pass

    async def collection_info(self, name: str) -> dict[str, Any]:
        """Get collection information."""
        info = await self._async_client.get_collection(name)
        return {
            "name": name,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "status": str(info.status),
        }

    # ==================== Vector Operations ====================

    async def upsert(
        self,
        collection: str,
        id: int,
        vector: list[float] | "NDArray",
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Insert or update single vector."""
        if hasattr(vector, "tolist"):
            vector = vector.tolist()

        await self._async_client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=id,
                    vector=vector,
                    payload=payload or {},
                )
            ],
        )

        logger.debug("vector_upserted", collection=collection, id=id)

    def upsert_batch(
        self,
        collection: str,
        ids: list[int],
        vectors: list[list[float]] | "NDArray",
        payloads: list[dict[str, Any]] | None = None,
        batch_size: int = 100,
    ) -> int:
        """Batch upsert vectors (sync for performance)."""
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()

        payloads = payloads or [{} for _ in ids]

        points = [
            models.PointStruct(id=id_, vector=vec, payload=payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]

        total = 0
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self._sync_client.upsert(
                collection_name=collection,
                points=batch,
            )
            total += len(batch)

        logger.info("batch_upsert_complete", collection=collection, total=total)
        return total

    async def delete(self, collection: str, ids: list[int]) -> None:
        """Delete points by IDs."""
        await self._async_client.delete(
            collection_name=collection,
            points_selector=models.PointIdsList(points=ids),
        )

    # ==================== Search Operations ====================

    async def search(
        self,
        collection: str,
        query_vector: list[float] | "NDArray",
        limit: int = 20,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        if hasattr(query_vector, "tolist"):
            query_vector = query_vector.tolist()

        query_filter = self._build_filter(filters) if filters else None

        results = await self._async_client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            {"id": hit.id, "score": hit.score, **hit.payload}
            for hit in results
        ]

    def _build_filter(self, filters: dict[str, Any]) -> models.Filter:
        """Build Qdrant filter from dict."""
        conditions = []

        for key, value in filters.items():
            if key.startswith("min_"):
                field = key[4:]
                conditions.append(
                    models.FieldCondition(
                        key=field,
                        range=models.Range(gte=value),
                    )
                )
            elif key.startswith("max_"):
                field = key[4:]
                conditions.append(
                    models.FieldCondition(
                        key=field,
                        range=models.Range(lte=value),
                    )
                )
            elif isinstance(value, list):
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchAny(any=value),
                    )
                )
            elif isinstance(value, bool):
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )
            else:
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )

        return models.Filter(must=conditions)

    async def find_similar(
        self,
        collection: str,
        point_id: int,
        limit: int = 10,
        exclude_self: bool = True,
    ) -> list[dict[str, Any]]:
        """Find similar points to existing point."""
        points = await self._async_client.retrieve(
            collection_name=collection,
            ids=[point_id],
            with_vectors=True,
        )

        if not points:
            return []

        vector = points[0].vector

        query_filter = None
        if exclude_self:
            query_filter = models.Filter(
                must_not=[models.HasIdCondition(has_id=[point_id])]
            )

        results = await self._async_client.search(
            collection_name=collection,
            query_vector=vector,
            limit=limit,
            query_filter=query_filter,
        )

        return [
            {"id": hit.id, "score": hit.score, **hit.payload}
            for hit in results
        ]

    # ==================== Product-specific Methods ====================

    async def upsert_product(
        self,
        product_id: int,
        embedding: list[float] | "NDArray",
        title: str,
        marketplace_id: int,
        price: float,
        brand: str | None = None,
        category_id: int | None = None,
        is_available: bool = True,
        url: str | None = None,
        image_url: str | None = None,
        **extra_payload: Any,
    ) -> None:
        """Upsert product embedding with metadata."""
        payload = {
            "title": title,
            "marketplace_id": marketplace_id,
            "price": price,
            "brand": brand,
            "category_id": category_id,
            "is_available": is_available,
            "url": url,
            "image_url": image_url,
            **extra_payload,
        }

        payload = {k: v for k, v in payload.items() if v is not None}

        await self.upsert(PRODUCTS_COLLECTION, product_id, embedding, payload)

    async def search_products(
        self,
        query_vector: list[float] | "NDArray",
        limit: int = 20,
        marketplace_ids: list[int] | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        category_id: int | None = None,
        in_stock_only: bool = True,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search products with filters."""
        filters = {}

        if marketplace_ids:
            filters["marketplace_id"] = marketplace_ids
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if category_id is not None:
            filters["category_id"] = category_id
        if in_stock_only:
            filters["is_available"] = True

        return await self.search(
            collection=PRODUCTS_COLLECTION,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filters=filters if filters else None,
        )

    async def find_similar_products(
        self,
        product_id: int,
        limit: int = 10,
        same_marketplace: bool = False,
    ) -> list[dict[str, Any]]:
        """Find products similar to given product."""
        results = await self.find_similar(
            collection=PRODUCTS_COLLECTION,
            point_id=product_id,
            limit=limit + 10,
        )

        if not same_marketplace and results:
            source = await self._async_client.retrieve(
                collection_name=PRODUCTS_COLLECTION,
                ids=[product_id],
            )
            if source:
                source_marketplace = source[0].payload.get("marketplace_id")
                results = [
                    r for r in results
                    if r.get("marketplace_id") != source_marketplace
                ]

        return results[:limit]

    async def health_check(self) -> dict[str, Any]:
        """Check Qdrant connection health."""
        try:
            collections = await self._async_client.get_collections()
            return {
                "status": "healthy",
                "collections": [c.name for c in collections.collections],
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def close(self) -> None:
        """Close Qdrant connections."""
        await self._async_client.close()
        self._sync_client.close()


_qdrant_service: QdrantService | None = None


def get_qdrant_service(
    host: str = "localhost",
    port: int = 6333,
) -> QdrantService:
    """Get singleton Qdrant service."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService(host=host, port=port)
    return _qdrant_service
