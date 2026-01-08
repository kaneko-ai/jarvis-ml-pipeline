"""Prompts package."""
from .registry import PromptEntry, PromptRegistry, get_registry

__all__ = ["PromptRegistry", "PromptEntry", "get_registry"]
