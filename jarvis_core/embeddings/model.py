"""Deterministic Embedding Model (Phase 24).

Wraps Sentence Transformers with normalization and caching to ensure result reproducibility.
"""

from __future__ import annotations

import logging
import unicodedata
import re
from pathlib import Path
from typing import List, Union
import numpy as np

from jarvis_core.embeddings.sentence_transformer import SentenceTransformerEmbedding, EmbeddingModel
from jarvis_core.cache.kv_cache import KVCache

logger = logging.getLogger(__name__)


class DeterministicEmbeddingModel:
    """Wrapper around an embedding model to ensure deterministic outputs via cache and normalization."""

    def __init__(
        self,
        model_name: str = EmbeddingModel.MINILM.value,
        cache_dir: Path | None = None,
        use_cache: bool = True,
    ):
        self.model_name = model_name
        self.usage_cache = use_cache

        # Initialize internal embedder
        self._embedder = SentenceTransformerEmbedding(model_name=model_name, cache_dir=cache_dir)

        # Initialize KV cache
        if self.usage_cache:
            kv_path = cache_dir if cache_dir else Path("data/cache")
            self._cache = KVCache(kv_path, name=f"embed_{self._sanitize_name(model_name)}")
        else:
            self._cache = None

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Get embeddings for a list of texts with caching."""
        if isinstance(texts, str):
            texts = [texts]

        # 1. Normalize Inputs
        normalized_texts = [self._normalize_text(t) for t in texts]

        # 2. Check Cache
        vectors = []
        indices_to_compute = []
        texts_to_compute = []

        for i, text in enumerate(normalized_texts):
            if self._cache:
                cache_key = self._cache.generate_key(text, self.model_name)
                cached = self._cache.get(cache_key)
                if cached:
                    vectors.append(np.array(cached, dtype=np.float32))
                    continue

            # Not found or no cache
            vectors.append(None)
            indices_to_compute.append(i)
            texts_to_compute.append(text)

        # 3. Compute missing
        if texts_to_compute:
            logger.debug(f"Computing embeddings for {len(texts_to_compute)} inputs")
            computed_vectors = self._embedder.encode(texts_to_compute)

            for idx, vec in zip(indices_to_compute, computed_vectors):
                vectors[idx] = vec

                # Update Cache
                if self._cache:
                    cache_key = self._cache.generate_key(normalized_texts[idx], self.model_name)
                    # Convert numpy to list for JSON serialization
                    self._cache.set(cache_key, vec.tolist())

        return np.vstack(vectors)

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent embedding."""
        if not text:
            return ""

        # Unicode Normalization (NFKC)
        text = unicodedata.normalize("NFKC", text)

        # Whitespace normalization
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _sanitize_name(self, name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "_", name)

    @property
    def dimension(self) -> int:
        return self._embedder.dimension