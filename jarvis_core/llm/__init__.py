"""LLM package."""
# Re-export from llm_utils for backwards compatibility
# TODO(deprecate): Remove this compatibility layer after migration

from jarvis_core.llm_utils import LLMClient, Message

from .model_router import ModelRouter
from .ensemble import MultiModelEnsemble, EnsembleStrategy, EnsembleResult

__all__ = [
    "LLMClient",
    "Message",
    "ModelRouter",
    "MultiModelEnsemble",
    "EnsembleStrategy",
    "EnsembleResult",
]

