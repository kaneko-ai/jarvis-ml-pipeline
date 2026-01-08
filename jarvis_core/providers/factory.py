"""
JARVIS Provider Factory

config.yamlからプロバイダーを生成
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .api_embed import APIEmbedProvider
from .api_llm import APILLMProvider
from .base import EmbedProvider, LLMProvider, ProviderConfig, ProviderType
from .local_embed import LocalEmbedProvider
from .local_llm import LocalLLMProvider

logger = logging.getLogger(__name__)


def load_runtime_config(config_path: str = "config.yaml") -> dict:
    """設定ファイルからruntime設定を読み込み."""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}

    with open(path, encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    return config.get("runtime", {})


def get_llm_provider(
    provider_type: str | None = None,
    config_path: str = "config.yaml"
) -> LLMProvider:
    """LLMプロバイダーを取得.
    
    Args:
        provider_type: "api" | "local" | None (設定から読み込み)
        config_path: 設定ファイルパス
    
    Returns:
        LLMProvider
    """
    runtime = load_runtime_config(config_path)

    if provider_type is None:
        provider_type = runtime.get("llm_provider", "api")

    if provider_type == "local":
        local_config = runtime.get("local", {}).get("llm", {})
        config = ProviderConfig(
            provider_type=ProviderType.LOCAL,
            model=local_config.get("model", "qwen2.5"),
            backend=local_config.get("backend", "ollama"),
        )
        return LocalLLMProvider(config)
    else:
        api_config = runtime.get("api", {}).get("llm", {})
        config = ProviderConfig(
            provider_type=ProviderType.API,
            model=api_config.get("model", "gpt-4o-mini"),
        )
        return APILLMProvider(config)


def get_embed_provider(
    provider_type: str | None = None,
    config_path: str = "config.yaml"
) -> EmbedProvider:
    """Embeddingプロバイダーを取得.
    
    Args:
        provider_type: "api" | "local" | None (設定から読み込み)
        config_path: 設定ファイルパス
    
    Returns:
        EmbedProvider
    """
    runtime = load_runtime_config(config_path)

    if provider_type is None:
        provider_type = runtime.get("embed_provider", "local")

    if provider_type == "local":
        local_config = runtime.get("local", {}).get("embed", {})
        config = ProviderConfig(
            provider_type=ProviderType.LOCAL,
            model=local_config.get("model", "paraphrase-multilingual-MiniLM-L12-v2"),
        )
        return LocalEmbedProvider(config)
    else:
        api_config = runtime.get("api", {}).get("embed", {})
        config = ProviderConfig(
            provider_type=ProviderType.API,
            model=api_config.get("model", "text-embedding-3-small"),
        )
        return APIEmbedProvider(config)
