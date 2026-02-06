"""OpenAI provider shim."""

from __future__ import annotations


class OpenAIProvider:
    """Minimal OpenAI provider."""

    def generate(self) -> str:
        """Return an empty response."""
        return ""
