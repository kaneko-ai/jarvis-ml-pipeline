"""Run manifest generation for reproducibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RunManifest:
    run_id: str
    timestamp: str
    targets: dict[str, Any]
    resolver_versions: dict[str, str]
    model_info: dict[str, Any]
    index_version: dict[str, Any]
    input_counts: dict[str, int]
    output_counts: dict[str, int]
    warnings_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "targets": self.targets,
            "resolver_versions": self.resolver_versions,
            "model_info": self.model_info,
            "index_version": self.index_version,
            "input_counts": self.input_counts,
            "output_counts": self.output_counts,
            "warnings_summary": self.warnings_summary,
        }


def create_run_manifest(
    run_id: str,
    targets: dict[str, Any],
    resolver_versions: dict[str, str],
    model_info: dict[str, Any],
    index_version: dict[str, Any],
    input_counts: dict[str, int],
    output_counts: dict[str, int],
    warnings_summary: dict[str, Any],
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        targets=targets,
        resolver_versions=resolver_versions,
        model_info=model_info,
        index_version=index_version,
        input_counts=input_counts,
        output_counts=output_counts,
        warnings_summary=warnings_summary,
    )
