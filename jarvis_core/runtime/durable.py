"""Durable Checkpoint.

Per RP-154, provides checkpoint/resume for long-running tasks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class CheckpointStage(Enum):
    """Stages for checkpointing."""

    FETCH = "fetch"
    PARSE = "parse"
    INDEX = "index"
    RETRIEVE = "retrieve"
    GENERATE = "generate"
    EVAL = "eval"
    COMPLETE = "complete"


@dataclass
class Checkpoint:
    """A checkpoint in task execution."""

    run_id: str
    stage: CheckpointStage
    step_id: int
    timestamp: str
    data: dict[str, Any]
    completed_items: list[str]
    pending_items: list[str]


class DurableRunner:
    """Runner with checkpoint/resume capability."""

    def __init__(self, run_id: str, checkpoint_dir: str = "data/checkpoints"):
        self.run_id = run_id
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoint_path = self.checkpoint_dir / f"{run_id}.checkpoint.json"
        self._current_stage = CheckpointStage.FETCH
        self._step_id = 0

    def save_checkpoint(
        self,
        stage: CheckpointStage,
        data: dict[str, Any],
        completed: list[str] = None,
        pending: list[str] = None,
    ) -> None:
        """Save a checkpoint.

        Args:
            stage: Current stage.
            data: Data to persist.
            completed: Completed item IDs.
            pending: Pending item IDs.
        """
        from datetime import datetime

        checkpoint = Checkpoint(
            run_id=self.run_id,
            stage=stage,
            step_id=self._step_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            data=data,
            completed_items=completed or [],
            pending_items=pending or [],
        )

        self._current_stage = stage
        self._step_id += 1

        with open(self._checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_id": checkpoint.run_id,
                    "stage": checkpoint.stage.value,
                    "step_id": checkpoint.step_id,
                    "timestamp": checkpoint.timestamp,
                    "data": checkpoint.data,
                    "completed_items": checkpoint.completed_items,
                    "pending_items": checkpoint.pending_items,
                },
                f,
                indent=2,
            )

    def load_checkpoint(self) -> Checkpoint | None:
        """Load existing checkpoint if any."""
        if not self._checkpoint_path.exists():
            return None

        with open(self._checkpoint_path, encoding="utf-8") as f:
            data = json.load(f)

        return Checkpoint(
            run_id=data["run_id"],
            stage=CheckpointStage(data["stage"]),
            step_id=data["step_id"],
            timestamp=data["timestamp"],
            data=data["data"],
            completed_items=data["completed_items"],
            pending_items=data["pending_items"],
        )

    def can_resume(self) -> bool:
        """Check if this run can be resumed."""
        return self._checkpoint_path.exists()

    def resume_from(self) -> CheckpointStage | None:
        """Get stage to resume from."""
        checkpoint = self.load_checkpoint()
        if checkpoint:
            return checkpoint.stage
        return None

    def clear_checkpoint(self) -> None:
        """Clear checkpoint after successful completion."""
        if self._checkpoint_path.exists():
            self._checkpoint_path.unlink()

    def get_completed_items(self) -> list[str]:
        """Get list of completed item IDs from checkpoint."""
        checkpoint = self.load_checkpoint()
        if checkpoint:
            return checkpoint.completed_items
        return []

    def get_pending_items(self) -> list[str]:
        """Get list of pending item IDs from checkpoint."""
        checkpoint = self.load_checkpoint()
        if checkpoint:
            return checkpoint.pending_items
        return []