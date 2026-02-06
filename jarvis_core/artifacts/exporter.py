"""Artifact export helpers."""

from __future__ import annotations

import json
from typing import Any


class ArtifactExporter:
    """Export artifacts to common formats."""

    def export(self, artifacts: list[Any], fmt: str = "json") -> str:
        """Export artifacts to a string.

        Args:
            artifacts: Artifacts to export.
            fmt: Export format ("json" supported).

        Returns:
            Serialized string.
        """
        if fmt == "json":
            return json.dumps(artifacts, ensure_ascii=False)
        return json.dumps(artifacts, ensure_ascii=False)


def export_artifacts(artifacts: list[Any], fmt: str = "json") -> str:
    """Export artifacts to a string.

    Args:
        artifacts: Artifacts to export.
        fmt: Export format ("json" supported).

    Returns:
        Serialized string.
    """
    return ArtifactExporter().export(artifacts, fmt=fmt)


__all__ = ["ArtifactExporter", "export_artifacts"]
