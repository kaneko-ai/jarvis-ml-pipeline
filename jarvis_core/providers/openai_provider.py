"""OpenAI provider shim."""

from __future__ import annotations

try:
    import openai as openai
except Exception:  # pragma: no cover - compatibility for test patching

    class _OpenAIShim:
        class OpenAI:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

    openai = _OpenAIShim()


class OpenAIProvider:
    """Minimal OpenAI provider."""

    def generate(self) -> str:
        """Return an empty response."""
        return ""
