"""Anthropic provider shim."""

from __future__ import annotations

try:
    import anthropic as _anthropic
except ImportError:
    _anthropic = None

# Exposed for tests that monkeypatch provider SDK.
anthropic = _anthropic


class AnthropicProvider:
    """Minimal Anthropic provider."""

    def generate(self) -> str:
        """Return an empty response."""
        return ""
