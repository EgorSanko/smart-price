"""Tests for ProductMatcher."""

import pytest
from unittest.mock import AsyncMock, Mock
import numpy as np


class TestProductMatcher:
    """Tests for ProductMatcher class."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        service = Mock()
        service.encode_product = AsyncMock(
            return_value=np.random.randn(256).astype(np.float32)
        )
        service.dimension = 256
        return service

    @pytest.fixture
    def mock_qdrant_service(self):
        """Create mock Qdrant service."""
        service = Mock()
        service.find_similar_products = AsyncMock(return_value=[
            {
                "id": 2,
                "title": "iPhone 15 Pro 256GB Black",
                "marketplace_id": 2,
                "price": 95000,
                "score": 0.92,
            },
            {
                "id": 3,
                "title": "Apple iPhone 15 Pro 256 ГБ",
                "marketplace_id": 3,
                "price": 89000,
                "score": 0.88,
            },
        ])
        service.search_products = AsyncMock(return_value=[
            {
                "id": 4,
                "title": "iPhone 15 Pro Max",
                "marketplace_id": 1,
                "price": 110000,
                "score": 0.85,
            },
        ])
        return service

    @pytest.fixture
    def matcher(self, mock_embedding_service, mock_qdrant_service):
        """Create ProductMatcher with mocks."""
        from app.ml.matching.matcher import ProductMatcher
        return ProductMatcher(mock_embedding_service, mock_qdrant_service)

    @pytest.mark.asyncio
    async def test_find_matches(self, matcher, mock_qdrant_service):
        """Should find matching products."""
        matches = await matcher.find_matches(product_id=1, limit=5)

        assert len(matches) == 2
        assert matches[0].score == 0.92
        assert matches[0].product_id == 2
        mock_qdrant_service.find_similar_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_matches_filters_low_scores(self, matcher, mock_qdrant_service):
        """Should filter matches below threshold."""
        mock_qdrant_service.find_similar_products.return_value = [
            {"id": 1, "title": "Test", "score": 0.5, "marketplace_id": 2, "price": 100},
        ]

        matches = await matcher.find_matches(product_id=1, min_score=0.7)

        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_find_matches_by_text(self, matcher, mock_embedding_service):
        """Should find matches by text query."""
        matches = await matcher.find_matches_by_text(
            title="iPhone 15 Pro",
            brand="Apple",
        )

        assert len(matches) >= 0
        mock_embedding_service.encode_product.assert_called_once()

    def test_classify_match_exact(self, matcher):
        """Should classify high scores as exact."""
        assert matcher._classify_match(0.96) == "exact"
        assert matcher._classify_match(0.95) == "exact"

    def test_classify_match_high_confidence(self, matcher):
        """Should classify medium scores as high_confidence."""
        assert matcher._classify_match(0.90) == "high_confidence"
        assert matcher._classify_match(0.85) == "high_confidence"

    def test_classify_match_partial(self, matcher):
        """Should classify lower scores as partial."""
        assert matcher._classify_match(0.75) == "partial"
        assert matcher._classify_match(0.70) == "partial"

    def test_normalize_brand(self, matcher):
        """Should normalize brand names."""
        assert matcher._normalize_brand("Apple") == "apple"
        assert matcher._normalize_brand("SAMSUNG") == "samsung"
        assert matcher._normalize_brand("Эппл") == "apple"
        assert matcher._normalize_brand("Сяоми") == "xiaomi"

    def test_extract_features_storage(self, matcher):
        """Should extract storage from title."""
        features = matcher._extract_features("iPhone 15 Pro 256GB")
        assert features["storage_gb"] == 256

        features = matcher._extract_features("MacBook Pro 1TB SSD")
        assert features["storage_gb"] == 1024

    def test_extract_features_color(self, matcher):
        """Should extract color from title."""
        features = matcher._extract_features("iPhone 15 Pro Black")
        assert features["color"] == "black"

        features = matcher._extract_features("iPhone 15 Pro Чёрный")
        assert features["color"] == "чёрный"

    def test_features_match_storage(self, matcher):
        """Should detect storage mismatch."""
        source = {"storage_gb": 256}
        target_match = {"storage_gb": 256}
        target_no_match = {"storage_gb": 512}

        assert matcher._features_match(source, target_match) is True
        assert matcher._features_match(source, target_no_match) is False

    @pytest.mark.asyncio
    async def test_compare_prices(self, matcher, mock_qdrant_service):
        """Should compare prices across marketplaces."""
        result = await matcher.compare_prices(product_id=1)

        assert "matches" in result
        assert "best_price" in result
        assert result["best_price"]["price"] == 89000


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_create_match_result(self):
        """Should create MatchResult."""
        from app.ml.matching.matcher import MatchResult

        result = MatchResult(
            product_id=123,
            marketplace_id=2,
            title="Test Product",
            price=1000.0,
            score=0.95,
            match_type="exact",
        )

        assert result.product_id == 123
        assert result.score == 0.95
        assert result.url is None
