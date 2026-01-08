"""
JARVIS Local LLM Provider

Ollama / vLLM 等のローカルLLM
"""

from __future__ import annotations

import logging

from .base import LLMProvider, ProviderConfig

logger = logging.getLogger(__name__)


class LocalLLMProvider(LLMProvider):
    """ローカルLLMプロバイダー."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None

    def initialize(self) -> None:
        """初期化."""
        if self._initialized:
            return

        backend = self.config.backend or "ollama"
        model = self.config.model or "qwen2.5"

        # バックエンド別の初期化
        if backend == "ollama":
            self._init_ollama(model)
        else:
            logger.warning(f"Unknown backend: {backend}, using mock")

        self._initialized = True
        logger.info(f"Local LLM provider initialized: {backend}/{model}")

    def _init_ollama(self, model: str) -> None:
        """Ollama初期化."""
        # Ollama client の初期化（実際はollama-pythonを使用）
        base_url = self.config.base_url or "http://localhost:11434"
        logger.info(f"Ollama backend: {base_url}, model: {model}")

    def is_available(self) -> bool:
        """利用可能かどうか."""
        # ローカルサーバーへの接続確認
        # 実際は http://localhost:11434/api/tags をチェック
        return True  # プレースホルダー

    def generate(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, **kwargs
    ) -> str:
        """テキスト生成."""
        if not self._initialized:
            self.initialize()

        # プレースホルダー実装
        logger.info(f"Local generate: backend={self.config.backend}, model={self.config.model}")
        return f"[Local Response for: {prompt[:50]}...]"

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """チャット形式で生成."""
        if not self._initialized:
            self.initialize()

        # プレースホルダー実装
        logger.info(f"Local chat: backend={self.config.backend}, messages={len(messages)}")
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"[Local Chat Response for: {last_user[:50]}...]"

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """コスト推定（ローカルは0）."""
        return 0.0
