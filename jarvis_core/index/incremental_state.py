"""Incremental State.

Per V4.2 Sprint 2, this provides hash-based state for incremental processing.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Any, Optional


@dataclass
class DocumentState:
    """State of a processed document."""

    doc_hash: str
    processed_at: datetime
    stages_completed: Set[str] = field(default_factory=set)
    chunk_count: int = 0

    def to_dict(self) -> dict:
        return {
            "doc_hash": self.doc_hash,
            "processed_at": self.processed_at.isoformat(),
            "stages_completed": list(self.stages_completed),
            "chunk_count": self.chunk_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentState":
        return cls(
            doc_hash=data["doc_hash"],
            processed_at=datetime.fromisoformat(data["processed_at"]),
            stages_completed=set(data.get("stages_completed", [])),
            chunk_count=data.get("chunk_count", 0),
        )


class IncrementalState:
    """Manages incremental processing state."""

    def __init__(self, state_path: Optional[str] = None):
        self.state_path = Path(state_path) if state_path else None
        self.documents: Dict[str, DocumentState] = {}
        self.chunk_hashes: Set[str] = set()

        if self.state_path and self.state_path.exists():
            self._load()

    def _load(self):
        """Load state from disk."""
        if not self.state_path or not self.state_path.exists():
            return

        with open(self.state_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for doc_hash, doc_data in data.get("documents", {}).items():
            self.documents[doc_hash] = DocumentState.from_dict(doc_data)

        self.chunk_hashes = set(data.get("chunk_hashes", []))

    def save(self):
        """Save state to disk."""
        if not self.state_path:
            return

        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "documents": {h: d.to_dict() for h, d in self.documents.items()},
            "chunk_hashes": list(self.chunk_hashes),
        }

        temp_path = self.state_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        temp_path.rename(self.state_path)

    def compute_item_hash(self, item: Any) -> str:
        """Compute hash for any item."""
        if isinstance(item, str):
            content = item
        elif isinstance(item, dict):
            content = json.dumps(item, sort_keys=True)
        else:
            content = str(item)

        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_processed(self, stage: str, item_hash: str) -> bool:
        """Check if item was processed in stage."""
        if item_hash in self.documents:
            return stage in self.documents[item_hash].stages_completed
        return False

    def mark_processed(
        self,
        stage: str,
        item_hash: str,
        chunk_count: int = 0,
    ) -> None:
        """Mark item as processed."""
        if item_hash not in self.documents:
            self.documents[item_hash] = DocumentState(
                doc_hash=item_hash,
                processed_at=datetime.now(),
            )

        self.documents[item_hash].stages_completed.add(stage)
        if chunk_count:
            self.documents[item_hash].chunk_count = chunk_count

    def add_chunk_hash(self, chunk_hash: str) -> bool:
        """Add chunk hash, return False if duplicate."""
        if chunk_hash in self.chunk_hashes:
            return False
        self.chunk_hashes.add(chunk_hash)
        return True

    def has_chunk(self, chunk_hash: str) -> bool:
        """Check if chunk exists."""
        return chunk_hash in self.chunk_hashes

    def get_stats(self) -> dict:
        """Get state statistics."""
        return {
            "documents": len(self.documents),
            "chunks": len(self.chunk_hashes),
            "stages": {
                stage: sum(
                    1 for d in self.documents.values()
                    if stage in d.stages_completed
                )
                for stage in ["ingest", "normalize", "chunk", "index"]
            },
        }

    def clear(self):
        """Clear all state."""
        self.documents.clear()
        self.chunk_hashes.clear()
