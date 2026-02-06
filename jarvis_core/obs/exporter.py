"""Observability export helpers."""

from __future__ import annotations

import json
from typing import Any


class ObservabilityExporter:
    """Export observability data."""

    def export(self, payload: dict[str, Any], fmt: str = "json") -> str:
        """Export payload to a string.

        Args:
            payload: Data to export.
            fmt: Export format ("json" supported).

        Returns:
            Serialized string.
        """
        if fmt == "json":
            return json.dumps(payload, ensure_ascii=False)
        return json.dumps(payload, ensure_ascii=False)


__all__ = ["ObservabilityExporter"]
