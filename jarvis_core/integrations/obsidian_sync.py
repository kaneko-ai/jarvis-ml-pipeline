"""Obsidian Incremental Sync.

Per V4-I01, this provides differential sync to Obsidian vault.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..bundle_v2 import BundleV2


def content_hash(text: str) -> str:
    """Calculate content hash."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


class ObsidianSync:
    """Incremental sync to Obsidian vault."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.index_file = self.vault_path / "JARVIS_INDEX.md"
        self.hash_file = self.vault_path / ".jarvis_hashes.json"
        self.hashes: Dict[str, str] = {}

        self._load_hashes()

    def _load_hashes(self):
        """Load existing hashes."""
        if self.hash_file.exists():
            with open(self.hash_file, "r", encoding="utf-8") as f:
                self.hashes = json.load(f)

    def _save_hashes(self):
        """Save hashes to file."""
        with open(self.hash_file, "w", encoding="utf-8") as f:
            json.dump(self.hashes, f, indent=2)

    def sync_note(self, note_id: str, content: str, folder: str = "") -> str:
        """Sync a single note.

        Args:
            note_id: Note identifier.
            content: Note content.
            folder: Optional subfolder.

        Returns:
            Status string (created, updated, unchanged).
        """
        new_hash = content_hash(content)

        if note_id in self.hashes and self.hashes[note_id] == new_hash:
            return "unchanged"

        # Write note
        if folder:
            note_dir = self.vault_path / folder
            note_dir.mkdir(parents=True, exist_ok=True)
            note_path = note_dir / f"{note_id}.md"
        else:
            note_path = self.vault_path / f"{note_id}.md"

        old_exists = note_path.exists()
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.hashes[note_id] = new_hash
        self._save_hashes()

        return "updated" if old_exists else "created"

    def sync_bundle(self, bundle: "BundleV2") -> dict:
        """Sync entire bundle to vault.

        Args:
            bundle: Bundle to sync.

        Returns:
            Sync result summary.
        """
        results = {"created": 0, "updated": 0, "unchanged": 0}

        # Sync index
        index_content = self._generate_index(bundle)
        status = self.sync_note("JARVIS_INDEX", index_content)
        results[status] += 1

        # Sync each artifact
        for i, artifact in enumerate(bundle.artifacts):
            note_id = f"artifact_{artifact.kind}_{i}"
            content = self._artifact_to_markdown(artifact)
            status = self.sync_note(note_id, content, folder="artifacts")
            results[status] += 1

        return results

    def _generate_index(self, bundle: "BundleV2") -> str:
        """Generate index note."""
        lines = [
            "# JARVIS Research Index",
            "",
            f"Last synced: {bundle.created_at.isoformat()}",
            "",
            "## Artifacts",
            "",
        ]

        for i, artifact in enumerate(bundle.artifacts):
            lines.append(f"- [[artifacts/artifact_{artifact.kind}_{i}|{artifact.kind}]]")

        return "\n".join(lines)

    def _artifact_to_markdown(self, artifact) -> str:
        """Convert artifact to markdown."""
        lines = [
            f"# {artifact.kind}",
            "",
        ]

        if artifact.facts:
            lines.append("## Facts")
            for f in artifact.facts:
                lines.append(f"- {f.statement}")
            lines.append("")

        if artifact.inferences:
            lines.append("## Inferences (推定)")
            for i in artifact.inferences:
                lines.append(f"- {i.statement}")
            lines.append("")

        if artifact.recommendations:
            lines.append("## Recommendations")
            for r in artifact.recommendations:
                lines.append(f"- {r.statement}")

        return "\n".join(lines)


def sync_to_obsidian(bundle: "BundleV2", vault_path: str) -> dict:
    """Convenience function to sync bundle to Obsidian."""
    syncer = ObsidianSync(vault_path)
    return syncer.sync_bundle(bundle)
