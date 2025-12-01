"""Lightweight execution engine for sequencing subtasks."""
from __future__ import annotations

from typing import List

from .planner import Planner
from .router import Router
from .task import Task, TaskStatus


class ExecutionEngine:
    """Coordinate planning and sequential execution via the router."""

    def __init__(self, planner: Planner, router: Router) -> None:
        self.planner = planner
        self.router = router

    def run(self, root_task: Task) -> List[Task]:
        """Plan and execute a root task, returning executed subtasks."""

        subtasks = self.planner.plan(root_task)
        executed: List[Task] = []

        for subtask in subtasks:
            if subtask.status == TaskStatus.PENDING:
                subtask.status = TaskStatus.RUNNING
            subtask.history.append({"event": "start", "status": subtask.status})

            result = self.router.run(subtask)

            subtask.history.append(
                {
                    "event": "complete",
                    "status": TaskStatus.DONE,
                    "result": getattr(result, "answer", None),
                    "meta": getattr(result, "meta", None),
                }
            )
            subtask.status = TaskStatus.DONE
            executed.append(subtask)

        return executed
