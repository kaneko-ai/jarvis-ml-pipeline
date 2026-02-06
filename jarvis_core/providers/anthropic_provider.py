"""Anthropic provider shim."""

from __future__ import annotations


class AnthropicProvider:
    """Minimal Anthropic provider."""

    def generate(self) -> str:
        """Return an empty response."""
        return ""
