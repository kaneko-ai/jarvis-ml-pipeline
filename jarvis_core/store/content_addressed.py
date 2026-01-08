"""Content-Addressed Store.

Per V4-B01, this provides content-addressed storage for inputs/extracts.
Same input → same hash (deterministic).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


def compute_hash(content: str | bytes) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content: String or bytes content.

    Returns:
        Hex digest of hash.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def verify_hash(content: str | bytes, expected_hash: str) -> bool:
    """Verify content against expected hash.

    Args:
        content: Content to verify.
        expected_hash: Expected hash value.

    Returns:
        True if hashes match.
    """
    return compute_hash(content) == expected_hash


@dataclass
class StoredObject:
    """A stored object with metadata."""

    hash: str
    content_type: str  # text, json, binary
    size_bytes: int
    created_at: str
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class ContentAddressedStore:
    """Content-addressed storage for reproducibility."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.objects_path = self.base_path / "objects"
        self.index_path = self.base_path / "index.json"
        self.index: dict = {}

        self._init_store()

    def _init_store(self):
        """Initialize store directories."""
        self.objects_path.mkdir(parents=True, exist_ok=True)
        if self.index_path.exists():
            with open(self.index_path, encoding="utf-8") as f:
                self.index = json.load(f)

    def _save_index(self):
        """Save index to disk."""
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def _get_object_path(self, hash: str) -> Path:
        """Get path for object by hash."""
        # Use first 2 chars as subdirectory
        return self.objects_path / hash[:2] / hash

    def store(
        self,
        content: str | bytes,
        content_type: str = "text",
        metadata: dict = None,
    ) -> str:
        """Store content and return hash.

        Args:
            content: Content to store.
            content_type: Type of content.
            metadata: Optional metadata.

        Returns:
            Content hash.
        """
        from datetime import datetime

        hash = compute_hash(content)

        # Check if already stored
        if hash in self.index:
            return hash

        # Store content
        obj_path = self._get_object_path(hash)
        obj_path.parent.mkdir(exist_ok=True)

        if isinstance(content, str):
            obj_path.write_text(content, encoding="utf-8")
            size = len(content.encode("utf-8"))
        else:
            obj_path.write_bytes(content)
            size = len(content)

        # Update index
        self.index[hash] = StoredObject(
            hash=hash,
            content_type=content_type,
            size_bytes=size,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {},
        ).to_dict()

        self._save_index()

        return hash

    def retrieve(self, hash: str) -> str | None:
        """Retrieve content by hash.

        Args:
            hash: Content hash.

        Returns:
            Content string, or None if not found.
        """
        if hash not in self.index:
            return None

        obj_path = self._get_object_path(hash)
        if not obj_path.exists():
            return None

        return obj_path.read_text(encoding="utf-8")

    def exists(self, hash: str) -> bool:
        """Check if hash exists in store."""
        return hash in self.index

    def get_metadata(self, hash: str) -> dict | None:
        """Get metadata for stored object."""
        if hash not in self.index:
            return None
        return self.index[hash]

    def list_objects(self) -> list[str]:
        """List all stored object hashes."""
        return list(self.index.keys())
