"""
JARVIS API Embed Provider

OpenAI / Cohere 等のAPIベースEmbedding
"""

from __future__ import annotations

import logging
import os

from .base import EmbedProvider, ProviderConfig

logger = logging.getLogger(__name__)


class APIEmbedProvider(EmbedProvider):
    """API Embeddingプロバイダー."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None
        self._dimension = 1536  # text-embedding-3-small

    def initialize(self) -> None:
        """初期化."""
        if self._initialized:
            return

        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No API key found for Embed provider")

        model = self.config.model or "text-embedding-3-small"
        if "3-large" in model:
            self._dimension = 3072

        self._initialized = True
        logger.info(f"API Embed provider initialized: {model}")

    def is_available(self) -> bool:
        """利用可能かどうか."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        return bool(api_key)

    def embed(self, text: str) -> list[float]:
        """単一テキストをベクトル化."""
        if not self._initialized:
            self.initialize()

        # プレースホルダー（実際はOpenAI APIを呼び出す）
        logger.debug(f"API embed: text length={len(text)}")
        return [0.0] * self._dimension

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """複数テキストをベクトル化."""
        if not self._initialized:
            self.initialize()

        logger.debug(f"API embed batch: count={len(texts)}")
        return [[0.0] * self._dimension for _ in texts]

    @property
    def dimension(self) -> int:
        """ベクトル次元数."""
        return self._dimension