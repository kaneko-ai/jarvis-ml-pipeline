"""
JARVIS Local Embed Provider

SentenceTransformers 等のローカルEmbedding
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .base import EmbedProvider, ProviderConfig

logger = logging.getLogger(__name__)


class LocalEmbedProvider(EmbedProvider):
    """ローカルEmbeddingプロバイダー."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._model = None
        self._dimension = 384  # paraphrase-multilingual-MiniLM-L12-v2
    
    def initialize(self) -> None:
        """初期化."""
        if self._initialized:
            return
        
        model_name = self.config.model or "paraphrase-multilingual-MiniLM-L12-v2"
        
        try:
            # SentenceTransformers のインポートは遅延
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Local Embed provider initialized: {model_name}, dim={self._dimension}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using mock")
            self._model = None
        
        self._initialized = True
    
    def is_available(self) -> bool:
        """利用可能かどうか."""
        try:
            import sentence_transformers
            return True
        except ImportError:
            return False
    
    def embed(self, text: str) -> List[float]:
        """単一テキストをベクトル化."""
        if not self._initialized:
            self.initialize()
        
        if self._model is None:
            return [0.0] * self._dimension
        
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
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
