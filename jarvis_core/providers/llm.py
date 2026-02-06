"""LLM provider compatibility helpers."""

from __future__ import annotations

from .api_llm import APILLMProvider
from .base import LLMProvider, ProviderConfig, ProviderType
from .local_llm import LocalLLMProvider


def get_llm_provider(config: ProviderConfig) -> LLMProvider:
    """Create an LLM provider based on config.

    Args:
        config: Provider configuration.

    Returns:
        LLMProvider instance.
    """
    if config.provider_type == ProviderType.LOCAL:
        return LocalLLMProvider(config)
    return APILLMProvider(config)


__all__ = ["APILLMProvider", "LocalLLMProvider", "LLMProvider", "get_llm_provider"]
