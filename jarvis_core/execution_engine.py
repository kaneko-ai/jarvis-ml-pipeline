"""Execution engine helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of an execution."""

    status: str = "ok"


class ExecutionEngine:
    """Minimal execution engine."""

    def run(self, task: str) -> ExecutionResult:
        """Run a task.

        Args:
            task: Task name.

        Returns:
            ExecutionResult.
        """
        _ = task
        return ExecutionResult(status="ok")


__all__ = ["ExecutionEngine", "ExecutionResult"]
