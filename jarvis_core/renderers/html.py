"""HTML renderer helpers."""

from __future__ import annotations


class HTMLRenderer:
    """Simple HTML renderer."""

    def render(self, content: str) -> str:
        """Render content as HTML.

        Args:
            content: Plain text content.

        Returns:
            HTML string.
        """
        return f"<div>{content}</div>"


__all__ = ["HTMLRenderer"]
