"""LaTeX renderer helpers."""

from __future__ import annotations


class LatexRenderer:
    """Simple LaTeX renderer."""

    def render(self, content: str) -> str:
        """Render content as LaTeX.

        Args:
            content: Plain text content.

        Returns:
            LaTeX string.
        """
        return content


__all__ = ["LatexRenderer"]
