# llm.py
"""Backwards compatibility wrapper for llm_utils."""
from .llm_utils import LLMClient, Message, Role

__all__ = ["LLMClient", "Message", "Role"]