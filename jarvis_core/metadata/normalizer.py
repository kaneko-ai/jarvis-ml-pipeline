"""Metadata normalization helpers."""

from __future__ import annotations

from typing import Any

from .normalize import audit_records, normalize_doi, normalize_record, normalize_title


class MetadataNormalizer:
    """Wrapper class for metadata normalization."""

    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize a metadata record.

        Args:
            record: Metadata dictionary.

        Returns:
            Normalized metadata dictionary.
        """
        return normalize_record(record)


__all__ = [
    "MetadataNormalizer",
    "audit_records",
    "normalize_doi",
    "normalize_record",
    "normalize_title",
]
