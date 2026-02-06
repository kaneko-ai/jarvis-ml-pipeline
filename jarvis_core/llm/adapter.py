"""Legacy HTTP adapter for LLM access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class LLMRequest:
    """Request payload for an LLM call."""

    prompt: str = ""
    max_tokens: int = 256
    temperature: float = 0.7
    metadata: dict[str, Any] | None = None


@dataclass
class LLMResponse:
    """Response payload for an LLM call."""

    content: str = ""
    raw: dict[str, Any] | None = None


class LLMAdapter:
    """Simple HTTP-based adapter with an OpenAI-style schema."""

    def __init__(self, endpoint: str = "http://localhost:8000/v1/chat/completions") -> None:
        """Initialize the adapter.

        Args:
            endpoint: HTTP endpoint for chat completions.
        """
        self.endpoint = endpoint

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a response for a prompt.

        Args:
            prompt: Prompt string.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with content and raw payload.
        """
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            response = requests.post(self.endpoint, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return LLMResponse(content=content, raw=data)
        except Exception:
            return LLMResponse(content="", raw=None)


__all__ = [
    "LLMAdapter",
    "LLMRequest",
    "LLMResponse",
]
