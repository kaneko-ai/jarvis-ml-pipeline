"""Checkpoint Manager (Phase 32).

Handles saving and loading of pipeline execution state to support resume capability.
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Dict, Any, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CheckpointState:
    """Snapshot of execution state."""

    run_id: str
    current_stage: str
    processed_items: Set[str] = field(default_factory=set)
    failed_items: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "current_stage": self.current_stage,
            "processed_items": list(self.processed_items),
            "failed_items": self.failed_items,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CheckpointState:
        return cls(
            run_id=data["run_id"],
            current_stage=data["current_stage"],
            processed_items=set(data.get("processed_items", [])),
            failed_items=data.get("failed_items", {}),
            metadata=data.get("metadata", {}),
        )


class CheckpointManager:
    """Persists pipeline state."""

    def __init__(self, checkpoint_dir: Path, run_id: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.file_path = self.checkpoint_dir / f"{run_id}_checkpoint.json"

        # Load existing or create new
        self.state = self._load()

    def _load(self) -> CheckpointState:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Loaded checkpoint for run {self.run_id}")
                return CheckpointState.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint {self.file_path}: {e}")

        return CheckpointState(run_id=self.run_id, current_stage="init")

    def save(self):
        """Save current state to disk."""
        try:
            temp_path = self.file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, indent=2)
            temp_path.replace(self.file_path)
            logger.debug(f"Saved checkpoint for {self.run_id}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def mark_processed(self, item_id: str):
        """Mark an item as successfully processed."""
        self.state.processed_items.add(item_id)
        # Note: We don't save on every item to avoid I/O bottleneck
        # Caller should call save() periodically or at end of batch

    def mark_failed(self, item_id: str, error: str):
        """Mark an item as failed."""
        self.state.failed_items[item_id] = error

    def set_stage(self, stage: str):
        """Update current pipeline stage."""
        self.state.current_stage = stage
        self.save()

    def is_processed(self, item_id: str) -> bool:
        """Check if item is already processed."""
        return item_id in self.state.processed_items