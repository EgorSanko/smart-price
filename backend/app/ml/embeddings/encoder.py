"""Embedding encoder for product text vectorization.

Supports multiple backends:
- OpenAI API (text-embedding-3-small) - recommended
- TF-IDF fallback - for testing without API

Example:
    >>> service = EmbeddingService()
    >>> embedding = await service.encode("iPhone 15 Pro Max 256GB")
    >>> print(len(embedding))  # 1536 for OpenAI, 256 for TF-IDF
"""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
import structlog

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = structlog.get_logger()


class BaseEncoder(ABC):
    """Abstract base class for embedding encoders."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass

    @abstractmethod
    async def encode(self, text: str) -> NDArray[np.float32]:
        """Encode single text into embedding vector."""
        pass

    @abstractmethod
    async def encode_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Encode multiple texts into embedding vectors."""
        pass


class OpenAIEncoder(BaseEncoder):
    """OpenAI text-embedding-3-small encoder.

    Uses OpenAI API for high-quality multilingual embeddings.
    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
    ) -> None:
        """Initialize OpenAI encoder."""
        import openai

        self.model = model
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._dimension = 1536

        logger.info("openai_encoder_initialized", model=model)

    @property
    def dimension(self) -> int:
        return self._dimension

    async def encode(self, text: str) -> NDArray[np.float32]:
        """Encode text using OpenAI API."""
        text = self._preprocess(text)

        response = await self._client.embeddings.create(
            model=self.model,
            input=text,
        )

        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)

    async def encode_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Encode multiple texts in one API call."""
        processed = [self._preprocess(t) for t in texts]

        response = await self._client.embeddings.create(
            model=self.model,
            input=processed,
        )

        embeddings = [d.embedding for d in response.data]
        return np.array(embeddings, dtype=np.float32)

    def _preprocess(self, text: str) -> str:
        """Preprocess text before encoding."""
        text = re.sub(r"\s+", " ", text).strip()
        return text[:30000]


class TFIDFEncoder(BaseEncoder):
    """Simple TF-IDF based encoder for testing.

    Uses hashing trick for fixed-dimension embeddings.
    No external dependencies required.
    """

    def __init__(self, dimension: int = 256) -> None:
        """Initialize TF-IDF encoder."""
        self._dimension = dimension
        logger.info("tfidf_encoder_initialized", dimension=dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    async def encode(self, text: str) -> NDArray[np.float32]:
        """Encode text using TF-IDF hashing."""
        return self._compute_embedding(text)

    async def encode_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Encode multiple texts."""
        embeddings = [self._compute_embedding(t) for t in texts]
        return np.array(embeddings, dtype=np.float32)

    def _compute_embedding(self, text: str) -> NDArray[np.float32]:
        """Compute TF-IDF embedding using hashing trick."""
        text = text.lower()
        words = re.findall(r"\w+", text)

        embedding = np.zeros(self._dimension, dtype=np.float32)

        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self._dimension
            sign = 1 if (h // self._dimension) % 2 == 0 else -1
            embedding[idx] += sign

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding /= norm

        return embedding


class EmbeddingService:
    """High-level embedding service for products.

    Automatically selects the best available encoder:
    1. OpenAI API (if OPENAI_API_KEY is set)
    2. TF-IDF fallback (for testing)

    Example:
        >>> service = EmbeddingService()
        >>> emb = await service.encode_product(product)
    """

    def __init__(
        self,
        encoder: BaseEncoder | None = None,
        use_cache: bool = True,
    ) -> None:
        """Initialize embedding service."""
        self._encoder = encoder or self._auto_select_encoder()
        self._use_cache = use_cache
        self._cache: dict[str, NDArray[np.float32]] = {}

        logger.info(
            "embedding_service_initialized",
            encoder=type(self._encoder).__name__,
            dimension=self.dimension,
        )

    @property
    def encoder(self) -> BaseEncoder:
        """Get active encoder."""
        return self._encoder

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._encoder.dimension

    def _auto_select_encoder(self) -> BaseEncoder:
        """Auto-select best available encoder."""
        import os

        if os.getenv("OPENAI_API_KEY"):
            try:
                return OpenAIEncoder()
            except Exception as e:
                logger.warning("openai_encoder_failed", error=str(e))

        logger.warning("using_tfidf_fallback")
        return TFIDFEncoder()

    async def encode(self, text: str) -> NDArray[np.float32]:
        """Encode text into embedding."""
        if self._use_cache:
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in self._cache:
                return self._cache[cache_key]

        embedding = await self._encoder.encode(text)

        if self._use_cache:
            self._cache[cache_key] = embedding

        return embedding

    async def encode_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Encode multiple texts."""
        return await self._encoder.encode_batch(texts)

    async def encode_product(
        self,
        product: dict,
        include_description: bool = True,
    ) -> NDArray[np.float32]:
        """Encode product for vector search."""
        text = self._build_product_text(product, include_description)
        return await self.encode(text)

    def _build_product_text(
        self,
        product: dict,
        include_description: bool = True,
    ) -> str:
        """Build text representation for product encoding."""
        parts = []

        if title := product.get("title"):
            parts.append(title)

        if brand := product.get("brand"):
            parts.append(f"бренд: {brand}")

        if category := product.get("category_name"):
            parts.append(f"категория: {category}")

        if include_description and (desc := product.get("description")):
            parts.append(desc[:500])

        return " ".join(parts)

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._cache.clear()
        logger.info("embedding_cache_cleared")


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
