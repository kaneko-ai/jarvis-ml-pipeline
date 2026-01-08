"""Retrieval Snapshot Management (Phase 2-ΩΩ).

Saves and restores paper retrieval results for reproducible runs.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_snapshot(
    run_dir: Path,
    query: str,
    source: str,
    included_ids: list[str],
    excluded_ids: list[dict[str, Any]] = None,
) -> Path:
    """Save retrieval snapshot.

    Args:
        run_dir: Path to run directory
        query: Search query
        source: Database source (pubmed/openalex)
        included_ids: List of included paper IDs
        excluded_ids: List of dicts with excluded IDs and reasons

    Returns:
        Path to snapshot file
    """
    import datetime

    snapshot = {
        "query": query,
        "source": source,
        "retrieved_at": datetime.datetime.now().isoformat(),
        "included_ids": included_ids,
        "excluded_ids": excluded_ids or [],
        "version": "1.0",
    }

    snapshot_path = run_dir / "retrieval_snapshot.json"

    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    logger.info(f"Retrieval snapshot saved: {len(included_ids)} papers")

    return snapshot_path


def load_snapshot(snapshot_path: Path) -> dict[str, Any]:
    """Load retrieval snapshot.

    Args:
        snapshot_path: Path to snapshot file

    Returns:
        Snapshot dict
    """
    with open(snapshot_path, encoding="utf-8") as f:
        snapshot = json.load(f)

    return snapshot
