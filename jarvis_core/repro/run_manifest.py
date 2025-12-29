"""Run manifest generation for reproducibility."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class RunManifest:
    run_id: str
    timestamp: str
    targets: Dict[str, Any]
    resolver_versions: Dict[str, str]
    model_info: Dict[str, Any]
    index_version: Dict[str, Any]
    input_counts: Dict[str, int]
    output_counts: Dict[str, int]
    warnings_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
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
    targets: Dict[str, Any],
    resolver_versions: Dict[str, str],
    model_info: Dict[str, Any],
    index_version: Dict[str, Any],
    input_counts: Dict[str, int],
    output_counts: Dict[str, int],
    warnings_summary: Dict[str, Any],
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
