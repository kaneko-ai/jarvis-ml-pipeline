"""PDF renderer helpers."""

from __future__ import annotations


class PDFRenderer:
    """Simple PDF renderer stub."""

    def render(self, content: str) -> bytes:
        """Render content to PDF bytes.

        Args:
            content: Plain text content.

        Returns:
            PDF bytes placeholder.
        """
        return content.encode("utf-8")


__all__ = ["PDFRenderer"]
