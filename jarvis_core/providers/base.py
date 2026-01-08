"""
JARVIS Provider Base Classes

Provider Switch: API / Local / Hybrid 切替の抽象化
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderType(Enum):
    """プロバイダータイプ."""
    API = "api"
    LOCAL = "local"
    HYBRID = "hybrid"


@dataclass
class ProviderConfig:
    """プロバイダー設定."""
    provider_type: ProviderType = ProviderType.API
    model: str = ""
    backend: str = ""  # ollama, vllm, etc.
    api_key: str | None = None
    base_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProviderConfig:
        """辞書から生成."""
        return cls(
            provider_type=ProviderType(data.get("type", "api")),
            model=data.get("model", ""),
            backend=data.get("backend", ""),
            api_key=data.get("api_key"),
            base_url=data.get("base_url"),
            extra=data.get("extra", {}),
        )


class BaseProvider(ABC):
    """プロバイダー基底クラス."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """初期化."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """利用可能かどうか."""
        pass

    @property
    def provider_type(self) -> ProviderType:
        """プロバイダータイプを取得."""
        return self.config.provider_type


class LLMProvider(BaseProvider):
    """LLMプロバイダー基底クラス."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """テキスト生成."""
        pass

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """チャット形式で生成."""
        pass

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """コスト推定（デフォルト: 0）."""
        return 0.0


class EmbedProvider(BaseProvider):
    """Embeddingプロバイダー基底クラス."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """単一テキストをベクトル化."""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """複数テキストをベクトル化."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """ベクトル次元数."""
        pass
