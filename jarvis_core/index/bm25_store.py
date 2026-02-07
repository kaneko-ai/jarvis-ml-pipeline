"""BM25 Index Persistence.

Per RP-116, persists BM25 index with IndexRegistry.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class IndexMetadata:
    """Metadata for a persisted index."""

    index_id: str
    index_type: str
    build_params: dict[str, Any]
    inputs_hash: str
    doc_count: int
    created_at: str
    version: str = "1.0"


class BM25IndexStore:
    """Persistent storage for BM25 indices."""

    def __init__(self, storage_dir: str = "data/indices"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _index_path(self, index_id: str) -> Path:
        return self.storage_dir / f"{index_id}.pkl"

    def _meta_path(self, index_id: str) -> Path:
        return self.storage_dir / f"{index_id}.meta.json"

    def save(
        self,
        index_id: str,
        index_data: Any,
        metadata: IndexMetadata,
    ) -> str:
        """Save index to disk.

        Args:
            index_id: Unique index identifier.
            index_data: The BM25 index object.
            metadata: Index metadata.

        Returns:
            Path to saved index.
        """
        index_path = self._index_path(index_id)
        meta_path = self._meta_path(index_id)

        # Save index
        with open(index_path, "wb") as f:
            pickle.dump(index_data, f)

        # Save metadata
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "index_id": metadata.index_id,
                    "index_type": metadata.index_type,
                    "build_params": metadata.build_params,
                    "inputs_hash": metadata.inputs_hash,
                    "doc_count": metadata.doc_count,
                    "created_at": metadata.created_at,
                    "version": metadata.version,
                },
                f,
                indent=2,
            )

        return str(index_path)

    def load(self, index_id: str) -> tuple[Any, IndexMetadata | None]:
        """Load index from disk.

        Args:
            index_id: Index identifier.

        Returns:
            (index_data, metadata) or (None, None) if not found.
        """
        index_path = self._index_path(index_id)
        meta_path = self._meta_path(index_id)

        if not index_path.exists():
            return None, None

        with open(index_path, "rb") as f:
            index_data = pickle.load(f)  # nosec B301: trusted on-disk index artifact

        metadata = None
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta_dict = json.load(f)
                metadata = IndexMetadata(**meta_dict)

        return index_data, metadata

    def exists(self, index_id: str) -> bool:
        """Check if index exists."""
        return self._index_path(index_id).exists()

    def get_metadata(self, index_id: str) -> IndexMetadata | None:
        """Get metadata for an index."""
        meta_path = self._meta_path(index_id)
        if not meta_path.exists():
            return None

        with open(meta_path, encoding="utf-8") as f:
            return IndexMetadata(**json.load(f))

    def list_indices(self) -> list[str]:
        """List all stored indices."""
        return [p.stem for p in self.storage_dir.glob("*.pkl")]

    def delete(self, index_id: str) -> bool:
        """Delete an index."""
        index_path = self._index_path(index_id)
        meta_path = self._meta_path(index_id)

        deleted = False
        if index_path.exists():
            index_path.unlink()
            deleted = True
        if meta_path.exists():
            meta_path.unlink()

        return deleted


def compute_inputs_hash(doc_ids: list[str]) -> str:
    """Compute hash of input document IDs for cache invalidation."""
    sorted_ids = sorted(doc_ids)
    content = "\n".join(sorted_ids)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def should_rebuild(
    store: BM25IndexStore,
    index_id: str,
    current_inputs_hash: str,
) -> bool:
    """Check if index should be rebuilt.

    Returns True if:
    - Index doesn't exist
    - Inputs have changed (different hash)
    """
    metadata = store.get_metadata(index_id)
    if metadata is None:
        return True

    return metadata.inputs_hash != current_inputs_hash
