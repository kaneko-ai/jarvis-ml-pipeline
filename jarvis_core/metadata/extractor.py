"""Metadata extraction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MetadataRecord:
    """Container for extracted metadata."""

    title: str = ""
    doi: str = ""
    extra: dict[str, Any] | None = None


class MetadataExtractor:
    """Minimal metadata extractor."""

    def extract(self, text: str) -> MetadataRecord:
        """Extract metadata from text.

        Args:
            text: Input text.

        Returns:
            MetadataRecord with best-effort fields.
        """
        if not text:
            return MetadataRecord()
        return MetadataRecord(title=text.strip()[:200], doi="", extra=None)


__all__ = ["MetadataExtractor", "MetadataRecord"]
