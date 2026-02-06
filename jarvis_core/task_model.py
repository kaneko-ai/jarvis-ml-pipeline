"""Task model helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskModel:
    """Simple task model."""

    task_id: str
    description: str = ""


__all__ = ["TaskModel"]
