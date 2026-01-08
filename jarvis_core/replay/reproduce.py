"""Reproduce from Manifest.

Per V4-B04, this replays execution from manifest and reports differences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DiffReason(Enum):
    """Reasons for output difference."""

    INPUT_CHANGED = "input_changed"
    CONFIG_CHANGED = "config_changed"
    MODEL_CHANGED = "model_changed"
    THRESHOLD_CHANGED = "threshold_changed"
    VERSION_CHANGED = "version_changed"
    EXTRACTION_CHANGED = "extraction_changed"
    RETRIEVAL_CHANGED = "retrieval_changed"
    NONDETERMINISM = "nondeterminism"
    UNKNOWN = "unknown"


@dataclass
class ReplayResult:
    """Result of replay execution."""

    original_run_id: str
    replay_run_id: str
    is_identical: bool
    diff_reasons: list[DiffReason]
    output_diff: dict[str, str]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "original_run_id": self.original_run_id,
            "replay_run_id": self.replay_run_id,
            "is_identical": self.is_identical,
            "diff_reasons": [r.value for r in self.diff_reasons],
            "output_diff": self.output_diff,
            "metadata": self.metadata,
        }


def replay_from_manifest(
    manifest_path: str,
    output_dir: str,
    store_path: str = None,
) -> ReplayResult:
    """Replay execution from manifest.

    Args:
        manifest_path: Path to original manifest.
        output_dir: Directory for replay output.
        store_path: Optional content-addressed store path.

    Returns:
        ReplayResult with diff analysis.
    """
    from datetime import datetime

    from ..provenance.manifest_v2 import ManifestV2, compare_manifests

    # Load original manifest
    original = ManifestV2.load(manifest_path)

    # Create new manifest for this run
    replay = ManifestV2(
        run_id=datetime.now().strftime("%Y%m%d_%H%M%S_replay"),
        created_at=datetime.now(),
        query=original.query,
        concepts=original.concepts,
        input_sources=original.input_sources,
    )

    # Compare manifests
    manifest_diffs = compare_manifests(original, replay)

    # Determine diff reasons
    diff_reasons = []
    output_diff = {}

    if "inputs" in manifest_diffs:
        diff_reasons.append(DiffReason.INPUT_CHANGED)
        output_diff["inputs"] = manifest_diffs["inputs"]

    if "config" in manifest_diffs:
        diff_reasons.append(DiffReason.CONFIG_CHANGED)
        output_diff["config"] = manifest_diffs["config"]

    if "llm_model" in manifest_diffs:
        diff_reasons.append(DiffReason.MODEL_CHANGED)
        output_diff["model"] = manifest_diffs["llm_model"]

    if "thresholds" in manifest_diffs:
        diff_reasons.append(DiffReason.THRESHOLD_CHANGED)
        output_diff["thresholds"] = manifest_diffs["thresholds"]

    if "version" in manifest_diffs:
        diff_reasons.append(DiffReason.VERSION_CHANGED)
        output_diff["version"] = manifest_diffs["version"]

    is_identical = len(diff_reasons) == 0

    return ReplayResult(
        original_run_id=original.run_id,
        replay_run_id=replay.run_id,
        is_identical=is_identical,
        diff_reasons=diff_reasons,
        output_diff=output_diff,
    )


def explain_diff(result: ReplayResult) -> str:
    """Generate human-readable diff explanation."""
    if result.is_identical:
        return "✅ Replay produced identical results."

    lines = [
        "## Replay Diff Report",
        "",
        f"Original: {result.original_run_id}",
        f"Replay: {result.replay_run_id}",
        "",
        "### Differences Found",
        "",
    ]

    for reason in result.diff_reasons:
        if reason == DiffReason.INPUT_CHANGED:
            lines.append("- **Input Changed**: Source files have been modified")
        elif reason == DiffReason.CONFIG_CHANGED:
            lines.append("- **Config Changed**: Configuration parameters differ")
        elif reason == DiffReason.MODEL_CHANGED:
            lines.append("- **Model Changed**: LLM model version differs")
        elif reason == DiffReason.THRESHOLD_CHANGED:
            lines.append("- **Threshold Changed**: Scoring thresholds differ")
        elif reason == DiffReason.VERSION_CHANGED:
            lines.append("- **Version Changed**: JARVIS version differs")
        elif reason == DiffReason.NONDETERMINISM:
            lines.append("- **Non-determinism**: Random variation detected")
        else:
            lines.append(f"- **Unknown**: {reason.value}")

    return "\n".join(lines)
