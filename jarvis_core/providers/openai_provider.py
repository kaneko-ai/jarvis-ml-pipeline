"""OpenAI provider shim."""

from __future__ import annotations

try:
    import openai as _openai
except ImportError:
    _openai = None

# Exposed for tests that monkeypatch provider SDK.
openai = _openai


class OpenAIProvider:
    """Minimal OpenAI provider."""

    def generate(self) -> str:
        """Return an empty response."""
        return ""
