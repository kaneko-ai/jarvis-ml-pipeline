"""LLM package.

Local-First LLM infrastructure with Ollama, llama.cpp, and cloud fallback.
"""
# Re-export from llm_utils for backwards compatibility
# TODO(deprecate): Remove this compatibility layer after migration

from jarvis_core.llm_utils import LLMClient, Message

from .model_router import ModelRouter, get_router, route_task, TaskType, ModelProvider
from .ensemble import MultiModelEnsemble, EnsembleStrategy, EnsembleResult
from .ollama_adapter import OllamaAdapter, OllamaConfig, get_ollama_adapter
from .llamacpp_adapter import LlamaCppAdapter, LlamaCppConfig, get_llamacpp_adapter

__all__ = [
    # Legacy
    "LLMClient",
    "Message",
    # Router
    "ModelRouter",
    "get_router",
    "route_task",
    "TaskType",
    "ModelProvider",
    # Ensemble
    "MultiModelEnsemble",
    "EnsembleStrategy",
    "EnsembleResult",
    # Local adapters
    "OllamaAdapter",
    "OllamaConfig",
    "get_ollama_adapter",
    "LlamaCppAdapter",
    "LlamaCppConfig",
    "get_llamacpp_adapter",
]
