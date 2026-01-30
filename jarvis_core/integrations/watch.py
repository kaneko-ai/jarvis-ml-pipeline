"""Watch Mode & Manifest Ingest.

Per V4-I02, this provides manifest-based input management.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ManifestEntry:
    """Entry in the input manifest."""

    path: str
    type: str  # pdf, url
    status: str = "pending"  # pending, processed, error
    added_at: str = ""
    processed_at: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "type": self.type,
            "status": self.status,
            "added_at": self.added_at,
            "processed_at": self.processed_at,
            "error": self.error,
        }


class ManifestWatcher:
    """Watch and process manifest file."""

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.entries: list[ManifestEntry] = []
        self._load()

    def _load(self):
        """Load manifest from file."""
        if self.manifest_path.exists():
            with open(self.manifest_path, encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [ManifestEntry(**e) for e in data.get("entries", [])]

    def _save(self):
        """Save manifest to file."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "entries": [e.to_dict() for e in self.entries],
                },
                f,
                indent=2,
            )

    def add_entry(self, path: str, entry_type: str = "pdf") -> None:
        """Add entry to manifest."""
        from datetime import datetime

        entry = ManifestEntry(
            path=path,
            type=entry_type,
            added_at=datetime.now().isoformat(),
        )
        self.entries.append(entry)
        self._save()

    def get_pending(self) -> list[ManifestEntry]:
        """Get pending entries."""
        return [e for e in self.entries if e.status == "pending"]

    def mark_processed(self, path: str) -> None:
        """Mark entry as processed."""
        from datetime import datetime

        for entry in self.entries:
            if entry.path == path:
                entry.status = "processed"
                entry.processed_at = datetime.now().isoformat()
                break
        self._save()

    def mark_error(self, path: str, error: str) -> None:
        """Mark entry as error."""
        for entry in self.entries:
            if entry.path == path:
                entry.status = "error"
                entry.error = error
                break
        self._save()

    def process_pending(
        self,
        processor: Callable[[str, str], None],
    ) -> dict:
        """Process all pending entries.

        Args:
            processor: Function that takes (path, type) and processes.

        Returns:
            Processing result summary.
        """
        results = {"processed": 0, "errors": 0}

        for entry in self.get_pending():
            try:
                processor(entry.path, entry.type)
                self.mark_processed(entry.path)
                results["processed"] += 1
            except Exception as e:
                self.mark_error(entry.path, str(e))
                results["errors"] += 1

        return results


def watch_manifest(
    manifest_path: str,
    processor: Callable[[str, str], None],
    interval_seconds: int = 60,
    once: bool = False,
) -> None:
    """Watch manifest and process new entries.

    Args:
        manifest_path: Path to manifest file.
        processor: Function to process entries.
        interval_seconds: Check interval.
        once: Run only once (for testing).
    """
    watcher = ManifestWatcher(manifest_path)

    while True:
        results = watcher.process_pending(processor)

        if results["processed"] > 0 or results["errors"] > 0:
            print(f"Processed: {results['processed']}, Errors: {results['errors']}")

        if once:
            break

        time.sleep(interval_seconds)


def create_manifest(entries: list[dict], output_path: str) -> None:
    """Create a new manifest file.

    Args:
        entries: List of {"path": str, "type": str} dicts.
        output_path: Path to save manifest.
    """
    watcher = ManifestWatcher(output_path)
    for e in entries:
        watcher.add_entry(e["path"], e.get("type", "pdf"))