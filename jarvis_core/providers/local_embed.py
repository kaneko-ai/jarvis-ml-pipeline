"""
JARVIS Local Embed Provider

SentenceTransformers 等のローカルEmbedding
Per JARVIS_LOCALFIRST_ROADMAP Task 1.2: ローカル埋め込み
"""

from __future__ import annotations

import logging
from enum import Enum

from .base import EmbedProvider, ProviderConfig

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """Available embedding models."""
    MINILM = "all-MiniLM-L6-v2"
    MINILM_MULTILINGUAL = "paraphrase-multilingual-MiniLM-L12-v2"
    SPECTER2 = "allenai/specter2"
    MPNET = "all-mpnet-base-v2"


# Model configurations
MODEL_CONFIG = {
    EmbeddingModel.MINILM: {
        "dimension": 384,
        "speed": "fast",
        "memory_mb": 250,
        "use_case": "general",
    },
    EmbeddingModel.MINILM_MULTILINGUAL: {
        "dimension": 384,
        "speed": "fast",
        "memory_mb": 500,
        "use_case": "multilingual",
    },
    EmbeddingModel.SPECTER2: {
        "dimension": 768,
        "speed": "medium",
        "memory_mb": 500,
        "use_case": "scientific",
    },
    EmbeddingModel.MPNET: {
        "dimension": 768,
        "speed": "medium",
        "memory_mb": 420,
        "use_case": "high_quality",
    },
}


class LocalEmbedProvider(EmbedProvider):
    """ローカルEmbeddingプロバイダー.
    
    Supports multiple models:
    - all-MiniLM-L6-v2: General purpose, fast (384d)
    - paraphrase-multilingual-MiniLM-L12-v2: Multilingual (384d)
    - allenai/specter2: Scientific papers (768d)
    - all-mpnet-base-v2: High quality (768d)
    """

    def __init__(
        self,
        config: ProviderConfig | None = None,
        model: EmbeddingModel | None = None,
    ):
        if config is None:
            from .base import ProviderConfig, ProviderType
            config = ProviderConfig(provider_type=ProviderType.LOCAL)

        super().__init__(config)

        # Determine model
        if model:
            self._model_enum = model
            self._model_name = model.value
        else:
            self._model_name = config.model or EmbeddingModel.MINILM.value
            self._model_enum = self._get_model_enum(self._model_name)

        self._model = None
        self._dimension = MODEL_CONFIG.get(
            self._model_enum,
            {"dimension": 384}
        )["dimension"]

    def _get_model_enum(self, model_name: str) -> EmbeddingModel:
        """Get model enum from name."""
        for model in EmbeddingModel:
            if model.value == model_name:
                return model
        return EmbeddingModel.MINILM

    @classmethod
    def for_scientific(cls) -> LocalEmbedProvider:
        """Create provider optimized for scientific papers."""
        return cls(model=EmbeddingModel.SPECTER2)

    @classmethod
    def for_multilingual(cls) -> LocalEmbedProvider:
        """Create provider for multilingual content."""
        return cls(model=EmbeddingModel.MINILM_MULTILINGUAL)

    @classmethod
    def for_general(cls) -> LocalEmbedProvider:
        """Create general-purpose provider (fast)."""
        return cls(model=EmbeddingModel.MINILM)

    def initialize(self) -> None:
        """初期化."""
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(
                f"Local Embed provider initialized: {self._model_name}, "
                f"dim={self._dimension}"
            )
        except ImportError:
            logger.warning("sentence-transformers not installed, using mock")
            self._model = None

        self._initialized = True

    def is_available(self) -> bool:
        """利用可能かどうか."""
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def embed(self, text: str) -> list[float]:
        """単一テキストをベクトル化."""
        if not self._initialized:
            self.initialize()

        if self._model is None:
            return [0.0] * self._dimension

        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """複数テキストをベクトル化."""
        if not self._initialized:
            self.initialize()

        if self._model is None:
            return [[0.0] * self._dimension for _ in texts]

        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]

    @property
    def dimension(self) -> int:
        """ベクトル次元数."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Current model name."""
        return self._model_name

    @property
    def model_info(self) -> dict:
        """Get model configuration info."""
        return MODEL_CONFIG.get(self._model_enum, {})

