"""Streaming Bundle & Checkpoint.

Per V4.2 Sprint 2, this provides incremental bundle writing and checkpoint/resume.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Checkpoint:
    """Checkpoint state for resumable execution."""

    checkpoint_id: str
    created_at: datetime
    completed_tasks: list[str]
    pending_tasks: list[str]
    task_results: dict[str, Any]
    manifest_hash: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "created_at": self.created_at.isoformat(),
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "task_results": {k: str(v)[:100] for k, v in self.task_results.items()},
            "manifest_hash": self.manifest_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Checkpoint:
        return cls(
            checkpoint_id=data["checkpoint_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_tasks=data["completed_tasks"],
            pending_tasks=data["pending_tasks"],
            task_results=data.get("task_results", {}),
            manifest_hash=data["manifest_hash"],
            metadata=data.get("metadata", {}),
        )


class StreamingBundle:
    """Atomic incremental bundle writing with checkpoint support."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.temp_dir = self.output_dir / ".streaming"
        self.checkpoint_file = self.temp_dir / "checkpoint.json"
        self.artifacts_dir = self.temp_dir / "artifacts"
        self.evidence_dir = self.temp_dir / "evidence"

        self._init_dirs()

    def _init_dirs(self):
        """Initialize directory structure."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.evidence_dir.mkdir(exist_ok=True)

    def write_artifact(self, artifact_id: str, data: dict) -> str:
        """Write artifact atomically.

        Args:
            artifact_id: Artifact identifier.
            data: Artifact data.

        Returns:
            Path to written file.
        """
        path = self.artifacts_dir / f"{artifact_id}.json"
        temp_path = path.with_suffix(".tmp")

        # Write to temp file first
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename
        temp_path.rename(path)

        return str(path)

    def write_evidence(self, chunk_id: str, content: str) -> str:
        """Write evidence chunk atomically."""
        path = self.evidence_dir / f"{chunk_id}.txt"
        temp_path = path.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)

        temp_path.rename(path)

        return str(path)

    def save_checkpoint(
        self,
        completed_tasks: list[str],
        pending_tasks: list[str],
        task_results: dict[str, Any],
        manifest_hash: str,
    ) -> Checkpoint:
        """Save checkpoint for resume capability.

        Args:
            completed_tasks: List of completed task IDs.
            pending_tasks: List of pending task IDs.
            task_results: Dict of task results.
            manifest_hash: Hash of current manifest.

        Returns:
            Saved checkpoint.
        """
        checkpoint = Checkpoint(
            checkpoint_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            created_at=datetime.now(),
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            task_results=task_results,
            manifest_hash=manifest_hash,
        )

        temp_path = self.checkpoint_file.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        temp_path.rename(self.checkpoint_file)

        return checkpoint

    def load_checkpoint(self) -> Checkpoint | None:
        """Load existing checkpoint if available."""
        if not self.checkpoint_file.exists():
            return None

        with open(self.checkpoint_file, encoding="utf-8") as f:
            data = json.load(f)

        return Checkpoint.from_dict(data)

    def can_resume(self, manifest_hash: str) -> bool:
        """Check if we can resume from checkpoint.

        Args:
            manifest_hash: Current manifest hash.

        Returns:
            True if resume is possible.
        """
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return False

        # Can only resume if manifest hasn't changed
        return checkpoint.manifest_hash == manifest_hash

    def finalize(self) -> str:
        """Finalize streaming bundle to output directory.

        Returns:
            Path to finalized bundle.
        """
        # Create final bundle.json
        artifacts = []
        for path in self.artifacts_dir.glob("*.json"):
            with open(path, encoding="utf-8") as f:
                artifacts.append(json.load(f))

        bundle_data = {
            "version": "v2",
            "created_at": datetime.now().isoformat(),
            "artifacts": artifacts,
            "evidence_count": len(list(self.evidence_dir.glob("*.txt"))),
        }

        # Write final bundle
        final_bundle = self.output_dir / "bundle.json"
        with open(final_bundle, "w", encoding="utf-8") as f:
            json.dump(bundle_data, f, indent=2, ensure_ascii=False)

        # Copy evidence to final location
        final_evidence = self.output_dir / "evidence"
        if final_evidence.exists():
            shutil.rmtree(final_evidence)
        if self.evidence_dir.exists():
            shutil.copytree(self.evidence_dir, final_evidence)

        # Create audit.md placeholder
        audit_path = self.output_dir / "audit.md"
        if not audit_path.exists():
            audit_path.write_text("# Audit Report\n\nGenerated by streaming bundle.\n")

        # Clean up temp directory
        shutil.rmtree(self.temp_dir)

        return str(self.output_dir)

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


def create_streaming_bundle(output_dir: str) -> StreamingBundle:
    """Create a new streaming bundle."""
    return StreamingBundle(output_dir)
