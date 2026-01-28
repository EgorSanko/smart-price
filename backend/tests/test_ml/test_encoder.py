"""Tests for embedding encoder."""

import pytest
import numpy as np
from unittest.mock import AsyncMock, Mock, patch


class TestTFIDFEncoder:
    """Tests for TF-IDF fallback encoder."""

    @pytest.mark.asyncio
    async def test_encode_returns_correct_dimension(self):
        """Should return embedding with correct dimension."""
        from app.ml.embeddings.encoder import TFIDFEncoder

        encoder = TFIDFEncoder(dimension=256)
        embedding = await encoder.encode("test product")

        assert embedding.shape == (256,)
        assert embedding.dtype == np.float32

    @pytest.mark.asyncio
    async def test_encode_is_normalized(self):
        """Should return L2-normalized embedding."""
        from app.ml.embeddings.encoder import TFIDFEncoder

        encoder = TFIDFEncoder()
        embedding = await encoder.encode("test product title")

        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_similar_texts_have_similar_embeddings(self):
        """Similar texts should produce similar embeddings."""
        from app.ml.embeddings.encoder import TFIDFEncoder

        encoder = TFIDFEncoder(dimension=256)

        emb1 = await encoder.encode("iPhone 15 Pro 256GB")
        emb2 = await encoder.encode("iPhone 15 Pro 256 ГБ")
        emb3 = await encoder.encode("Samsung Galaxy S24")

        sim_12 = np.dot(emb1, emb2)
        sim_13 = np.dot(emb1, emb3)

        assert sim_12 > sim_13

    @pytest.mark.asyncio
    async def test_encode_batch(self):
        """Should encode multiple texts."""
        from app.ml.embeddings.encoder import TFIDFEncoder

        encoder = TFIDFEncoder(dimension=128)
        texts = ["product 1", "product 2", "product 3"]

        embeddings = await encoder.encode_batch(texts)

        assert embeddings.shape == (3, 128)


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    def test_auto_selects_tfidf_without_api_key(self):
        """Should use TF-IDF when no API key."""
        from app.ml.embeddings.encoder import EmbeddingService, TFIDFEncoder

        with patch.dict("os.environ", {}, clear=True):
            service = EmbeddingService()
            assert isinstance(service.encoder, TFIDFEncoder)

    @pytest.mark.asyncio
    async def test_encode_product(self):
        """Should encode product dict."""
        from app.ml.embeddings.encoder import EmbeddingService, TFIDFEncoder

        service = EmbeddingService(encoder=TFIDFEncoder(dimension=128))

        product = {
            "title": "iPhone 15 Pro Max 256GB",
            "brand": "Apple",
            "description": "Flagship smartphone",
        }

        embedding = await service.encode_product(product)

        assert embedding.shape == (128,)

    @pytest.mark.asyncio
    async def test_caching(self):
        """Should cache embeddings."""
        from app.ml.embeddings.encoder import EmbeddingService, TFIDFEncoder

        encoder = TFIDFEncoder(dimension=64)
        service = EmbeddingService(encoder=encoder, use_cache=True)

        text = "test caching"

        emb1 = await service.encode(text)
        emb2 = await service.encode(text)

        np.testing.assert_array_equal(emb1, emb2)

    def test_clear_cache(self):
        """Should clear embedding cache."""
        from app.ml.embeddings.encoder import EmbeddingService, TFIDFEncoder

        service = EmbeddingService(encoder=TFIDFEncoder(), use_cache=True)
        service._cache["test"] = np.array([1, 2, 3])

        service.clear_cache()

        assert len(service._cache) == 0


class TestOpenAIEncoder:
    """Tests for OpenAI encoder (mocked)."""

    @pytest.mark.asyncio
    async def test_encode_calls_api(self):
        """Should call OpenAI API."""
        with patch("app.ml.embeddings.encoder.openai") as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.AsyncOpenAI.return_value = mock_client

            from app.ml.embeddings.encoder import OpenAIEncoder

            encoder = OpenAIEncoder(api_key="test-key")
            result = await encoder.encode("test text")

            assert result.shape == (1536,)
            mock_client.embeddings.create.assert_called_once()
