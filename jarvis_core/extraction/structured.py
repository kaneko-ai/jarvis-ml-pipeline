"""Structured extraction helpers."""

from __future__ import annotations


class StructuredExtractor:
    """Minimal structured extractor."""

    def extract(self) -> dict:
        """Return an empty structured payload."""
        return {"items": []}
