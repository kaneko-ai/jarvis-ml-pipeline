"""Sentence Transformer Embedding Module.

Provides dense vector embeddings using Sentence Transformers.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.2.1
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """Available embedding models with their configurations."""

    MINILM = "all-MiniLM-L6-v2"
    MINILM_MULTILINGUAL = "paraphrase-multilingual-MiniLM-L12-v2"
    SPECTER2 = "allenai/specter2"
    MPNET = "all-mpnet-base-v2"


@dataclass
class ModelConfig:
    """Configuration for an embedding model."""

    dimension: int
    speed: str  # "fast", "medium", "slow"
    memory_mb: int
    use_case: str


MODEL_CONFIGS = {
    EmbeddingModel.MINILM: ModelConfig(384, "fast", 250, "general"),
    EmbeddingModel.MINILM_MULTILINGUAL: ModelConfig(384, "fast", 500, "multilingual"),
    EmbeddingModel.SPECTER2: ModelConfig(768, "medium", 500, "scientific"),
    EmbeddingModel.MPNET: ModelConfig(768, "medium", 420, "high_quality"),
}


class SentenceTransformerEmbedding:
    """Dense embedding using Sentence Transformers.
    
    Supports multiple models optimized for different use cases:
    - all-MiniLM-L6-v2: Fast, general purpose (384d)
    - paraphrase-multilingual-MiniLM-L12-v2: Multilingual (384d)
    - allenai/specter2: Scientific papers (768d)
    - all-mpnet-base-v2: High quality (768d)
    
    Example:
        >>> embedder = SentenceTransformerEmbedding()
        >>> vectors = embedder.encode(["Hello world", "Scientific paper"])
        >>> print(vectors.shape)
        (2, 384)
    """

    def __init__(
        self,
        model_name: str | EmbeddingModel = EmbeddingModel.MINILM,
        device: str | None = None,
        batch_size: int = 32,
        cache_dir: Path | None = None,
    ):
        """Initialize the embedding model.
        
        Args:
            model_name: Model identifier or EmbeddingModel enum
            device: Device to use ("cpu", "cuda", "mps"). Auto-detect if None.
            batch_size: Batch size for encoding
            cache_dir: Directory for model cache
        """
        if isinstance(model_name, EmbeddingModel):
            self._model_enum = model_name
            self._model_name = model_name.value
        else:
            self._model_name = model_name
            self._model_enum = self._get_model_enum(model_name)

        self._device = device
        self._batch_size = batch_size
        self._cache_dir = cache_dir
        self._model = None
        self._initialized = False

        # Get dimension from config or default
        config = MODEL_CONFIGS.get(self._model_enum)
        self._dimension = config.dimension if config else 384

    def _get_model_enum(self, model_name: str) -> EmbeddingModel | None:
        """Get model enum from name."""
        for model in EmbeddingModel:
            if model.value == model_name:
                return model
        return None

    def _initialize(self) -> None:
        """Lazy initialization of the model."""
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer

            kwargs = {}
            if self._cache_dir:
                kwargs["cache_folder"] = str(self._cache_dir)
            if self._device:
                kwargs["device"] = self._device

            self._model = SentenceTransformer(self._model_name, **kwargs)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(
                f"SentenceTransformerEmbedding initialized: {self._model_name}, "
                f"dim={self._dimension}, device={self._model.device}"
            )
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            self._model = None
        except Exception as e:
            logger.error(f"Failed to load model {self._model_name}: {e}")
            self._model = None

        self._initialized = True

    def encode(self, texts: str | list[str]) -> np.ndarray:
        """Encode texts into dense vectors.
        
        Args:
            texts: Single text or list of texts to encode
            
        Returns:
            numpy array of shape (n_texts, dimension)
        """
        if isinstance(texts, str):
            texts = [texts]

        self._initialize()

        if self._model is None:
            # Fallback: return hash-based embeddings
            return self._hash_embeddings(texts)

        embeddings = self._model.encode(
            texts,
            batch_size=self._batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )

        return embeddings

    def _hash_embeddings(self, texts: list[str]) -> np.ndarray:
        """Fallback hash-based embeddings when model unavailable."""
        import hashlib

        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            numbers = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
            repeats = int(np.ceil(self._dimension / len(numbers)))
            tiled = np.tile(numbers, repeats)[:self._dimension]
            vec = tiled / 255.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)

        return np.vstack(vectors)

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    def is_available(self) -> bool:
        """Check if the model is available."""
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            return False

    @classmethod
    def for_scientific(cls) -> SentenceTransformerEmbedding:
        """Create embedder optimized for scientific papers."""
        return cls(model_name=EmbeddingModel.SPECTER2)

    @classmethod
    def for_multilingual(cls) -> SentenceTransformerEmbedding:
        """Create embedder for multilingual content."""
        return cls(model_name=EmbeddingModel.MINILM_MULTILINGUAL)

    @classmethod
    def for_general(cls) -> SentenceTransformerEmbedding:
        """Create fast, general-purpose embedder."""
        return cls(model_name=EmbeddingModel.MINILM)


def get_default_embedding_model() -> SentenceTransformerEmbedding:
    """Get the default embedding model.
    
    Returns all-MiniLM-L6-v2 as the default for speed and memory efficiency.
    """
    return SentenceTransformerEmbedding.for_general()
