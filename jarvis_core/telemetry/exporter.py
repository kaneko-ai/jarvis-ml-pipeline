"""Telemetry export helpers."""

from __future__ import annotations

import json
from typing import Any


class TelemetryExporter:
    """Export telemetry payloads."""

    def export(self, payload: dict[str, Any], fmt: str = "json") -> str:
        """Export telemetry payload.

        Args:
            payload: Telemetry data.
            fmt: Export format ("json" supported).

        Returns:
            Serialized string.
        """
        if fmt == "json":
            return json.dumps(payload, ensure_ascii=False)
        return json.dumps(payload, ensure_ascii=False)


__all__ = ["TelemetryExporter"]
