"""Anthropic provider shim."""

from __future__ import annotations

try:
    import anthropic as anthropic
except Exception:  # pragma: no cover - compatibility for test patching

    class _AnthropicShim:
        class Anthropic:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

    anthropic = _AnthropicShim()


class AnthropicProvider:
    """Minimal Anthropic provider."""

    def generate(self) -> str:
        """Return an empty response."""
        return ""
