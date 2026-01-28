"""Product matching across marketplaces.

Finds the same product on different marketplaces using:
1. Vector similarity search
2. Text normalization and comparison
3. Feature extraction (brand, model, specs)

Example:
    >>> matcher = ProductMatcher(embedding_service, qdrant_service)
    >>> matches = await matcher.find_matches(product_id=123)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from app.ml.embeddings import EmbeddingService
    from app.services.qdrant_service import QdrantService

logger = structlog.get_logger()


@dataclass
class MatchResult:
    """Result of product matching."""

    product_id: int
    marketplace_id: int
    title: str
    price: float
    score: float
    match_type: str
    url: str | None = None
    image_url: str | None = None


class ProductMatcher:
    """Match products across different marketplaces.

    Uses combination of:
    - Vector similarity for semantic matching
    - Text normalization for brand/model extraction
    - Heuristics for score adjustment
    """

    EXACT_MATCH_THRESHOLD = 0.95
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MATCH_THRESHOLD = 0.70

    def __init__(
        self,
        embedding_service: "EmbeddingService",
        qdrant_service: "QdrantService",
    ) -> None:
        """Initialize ProductMatcher."""
        self._embeddings = embedding_service
        self._qdrant = qdrant_service
        logger.info("product_matcher_initialized")

    async def find_matches(
        self,
        product_id: int,
        limit: int = 10,
        min_score: float | None = None,
        exclude_same_marketplace: bool = True,
    ) -> list[MatchResult]:
        """Find matching products for given product ID."""
        min_score = min_score or self.MATCH_THRESHOLD

        similar = await self._qdrant.find_similar_products(
            product_id=product_id,
            limit=limit * 2,
            same_marketplace=not exclude_same_marketplace,
        )

        if not similar:
            logger.info("no_similar_found", product_id=product_id)
            return []

        results = []
        for item in similar:
            score = item.get("score", 0)
            if score >= min_score:
                match_type = self._classify_match(score)
                results.append(
                    MatchResult(
                        product_id=item["id"],
                        marketplace_id=item.get("marketplace_id", 0),
                        title=item.get("title", ""),
                        price=item.get("price", 0),
                        score=score,
                        match_type=match_type,
                        url=item.get("url"),
                        image_url=item.get("image_url"),
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)

        logger.info(
            "matches_found",
            product_id=product_id,
            count=len(results),
            top_score=results[0].score if results else 0,
        )

        return results[:limit]

    async def find_matches_by_text(
        self,
        title: str,
        brand: str | None = None,
        description: str | None = None,
        limit: int = 10,
        min_score: float | None = None,
        marketplace_ids: list[int] | None = None,
    ) -> list[MatchResult]:
        """Find matching products by text query."""
        min_score = min_score or self.MATCH_THRESHOLD

        product = {
            "title": title,
            "brand": brand,
            "description": description,
        }

        embedding = await self._embeddings.encode_product(product)

        results = await self._qdrant.search_products(
            query_vector=embedding,
            limit=limit * 2,
            marketplace_ids=marketplace_ids,
            score_threshold=min_score,
        )

        matches = []
        for item in results:
            score = item.get("score", 0)

            if brand and item.get("brand"):
                if self._normalize_brand(brand) == self._normalize_brand(item["brand"]):
                    score = min(score * 1.1, 1.0)

            source_features = self._extract_features(title)
            target_features = self._extract_features(item.get("title", ""))

            if self._features_match(source_features, target_features):
                score = min(score * 1.1, 1.0)

            match_type = self._classify_match(score)
            matches.append(
                MatchResult(
                    product_id=item["id"],
                    marketplace_id=item.get("marketplace_id", 0),
                    title=item.get("title", ""),
                    price=item.get("price", 0),
                    score=score,
                    match_type=match_type,
                    url=item.get("url"),
                    image_url=item.get("image_url"),
                )
            )

        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:limit]

    async def compare_prices(
        self,
        product_id: int,
        min_confidence: float = 0.80,
    ) -> dict[str, Any]:
        """Compare prices of matching products across marketplaces."""
        matches = await self.find_matches(
            product_id=product_id,
            limit=20,
            min_score=min_confidence,
        )

        if not matches:
            return {
                "source_id": product_id,
                "matches": [],
                "best_price": None,
                "savings_percent": None,
            }

        prices = [m.price for m in matches if m.price > 0]
        if prices:
            best_price = min(prices)
            best_match = next(m for m in matches if m.price == best_price)
        else:
            best_price = None
            best_match = None

        return {
            "source_id": product_id,
            "matches": [
                {
                    "product_id": m.product_id,
                    "marketplace_id": m.marketplace_id,
                    "title": m.title,
                    "price": m.price,
                    "score": m.score,
                    "match_type": m.match_type,
                }
                for m in matches
            ],
            "best_price": {
                "price": best_price,
                "product_id": best_match.product_id if best_match else None,
                "marketplace_id": best_match.marketplace_id if best_match else None,
            } if best_match else None,
        }

    def _classify_match(self, score: float) -> str:
        """Classify match type based on score."""
        if score >= self.EXACT_MATCH_THRESHOLD:
            return "exact"
        elif score >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "high_confidence"
        else:
            return "partial"

    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand name for comparison."""
        brand = brand.lower().strip()

        replacements = {
            "эппл": "apple",
            "эпл": "apple",
            "самсунг": "samsung",
            "сяоми": "xiaomi",
            "ксяоми": "xiaomi",
            "хуавей": "huawei",
        }

        return replacements.get(brand, brand)

    def _extract_features(self, title: str) -> dict[str, Any]:
        """Extract product features from title."""
        title_lower = title.lower()
        features = {}

        memory_match = re.search(r"(\d+)\s*(gb|tb|гб|тб)", title_lower)
        if memory_match:
            value = int(memory_match.group(1))
            unit = memory_match.group(2)
            if unit in ("tb", "тб"):
                value *= 1024
            features["storage_gb"] = value

        colors = [
            "black", "white", "silver", "gold", "blue", "red",
            "черный", "чёрный", "белый", "серебристый", "золотой", "синий",
        ]
        for color in colors:
            if color in title_lower:
                features["color"] = color
                break

        return features

    def _features_match(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
    ) -> bool:
        """Check if extracted features match."""
        if "storage_gb" in source and "storage_gb" in target:
            if source["storage_gb"] != target["storage_gb"]:
                return False
        return True


_product_matcher: ProductMatcher | None = None


def get_product_matcher(
    embedding_service: "EmbeddingService",
    qdrant_service: "QdrantService",
) -> ProductMatcher:
    """Get singleton ProductMatcher."""
    global _product_matcher
    if _product_matcher is None:
        _product_matcher = ProductMatcher(embedding_service, qdrant_service)
    return _product_matcher
