"""Writing generator helpers."""

from __future__ import annotations


class WritingGenerator:
    """Minimal writing generator."""

    def generate(self, prompt: str) -> str:
        """Generate a draft for a prompt.

        Args:
            prompt: Prompt text.

        Returns:
            Draft text.
        """
        return f"Draft: {prompt}"


__all__ = ["WritingGenerator"]
