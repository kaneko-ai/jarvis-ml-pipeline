"""LLM package."""
# Re-export from original llm module for backwards compatibility
import sys
import importlib.util

# Load the original llm.py module
_spec = importlib.util.spec_from_file_location(
    "jarvis_core._llm_original",
    __file__.replace("llm/__init__.py", "llm.py").replace("llm\\__init__.py", "llm.py")
)
if _spec and _spec.loader:
    _module = importlib.util.module_from_spec(_spec)
    try:
        _spec.loader.exec_module(_module)
        LLMClient = _module.LLMClient
        Message = _module.Message
    except Exception:
        # Fallback definitions
        from dataclasses import dataclass
        from typing import Literal
        
        Role = Literal["system", "user", "assistant"]
        
        @dataclass
        class Message:
            role: Role
            content: str
        
        class LLMClient:
            def __init__(self, model: str = "gemini-2.0-flash", **kwargs):
                self.model = model
            def generate(self, messages, **kwargs):
                return "Fallback response"

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
