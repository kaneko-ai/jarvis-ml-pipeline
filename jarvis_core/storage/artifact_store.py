"""Artifact Store - manages run-scoped artifacts."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional


class ArtifactStore:
    """Manages artifacts for a run using relative paths."""

    def __init__(self, run_id: str, base_dir: str = "logs/runs"):
        self.run_id = run_id
        self.base_dir = Path(base_dir)
        self.artifacts_dir = self.base_dir / run_id / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, data: bytes | str, metadata: Optional[dict] = None) -> str:
        """Save an artifact.

        Returns:
            Relative path to artifact.
        """
        artifact_path = self.artifacts_dir / name

        if isinstance(data, str):
            artifact_path.write_text(data, encoding="utf-8")
        else:
            artifact_path.write_bytes(data)

        if metadata:
            meta_path = self.artifacts_dir / f"{name}.meta.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        return str(artifact_path.relative_to(self.base_dir))

    def load(self, name: str) -> Optional[bytes]:
        """Load an artifact."""
        artifact_path = self.artifacts_dir / name
        if artifact_path.exists():
            return artifact_path.read_bytes()
        return None

    def load_text(self, name: str) -> Optional[str]:
        """Load a text artifact."""
        artifact_path = self.artifacts_dir / name
        if artifact_path.exists():
            return artifact_path.read_text(encoding="utf-8")
        return None

    def list(self) -> list[str]:
        """List all artifacts."""
        return [f.name for f in self.artifacts_dir.iterdir() if not f.name.endswith(".meta.json")]

    def copy_from(self, source_path: str, name: Optional[str] = None) -> str:
        """Copy file into artifact store."""
        src = Path(source_path)
        dest_name = name or src.name
        shutil.copy2(src, self.artifacts_dir / dest_name)
        return str((self.artifacts_dir / dest_name).relative_to(self.base_dir))
