"""Lightweight execution engine for sequencing subtasks."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, List

from .planner import Planner
from .retry import RetryPolicy
from .task import Task, TaskStatus
from .validation import EvaluationResult

logger = logging.getLogger("jarvis_core.executor")

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .router import Router


class ExecutionEngine:
    """Coordinate planning and sequential execution via the router."""

    def __init__(
        self,
        planner: Planner,
        router: "Router",
        retry_policy: RetryPolicy | None = None,
        validator: Callable[[object], EvaluationResult] | None = None,
    ) -> None:
        self.planner = planner
        self.router = router
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=1)
        self.validator = validator

    def run(self, root_task: Task) -> List[Task]:
        """Plan and execute a root task, returning executed subtasks."""

        subtasks = self.planner.plan(root_task)
        executed: List[Task] = []

        for subtask in subtasks:
            if subtask.status == TaskStatus.PENDING:
                subtask.status = TaskStatus.RUNNING
            subtask.history.append({"event": "start", "status": subtask.status})

            result, evaluation, attempts = self._execute_with_retry(subtask)

            final_status = TaskStatus.DONE
            if evaluation and not evaluation.ok:
                final_status = TaskStatus.FAILED

            subtask.history.append(
                {
                    "event": "complete",
                    "status": final_status,
                    "result": getattr(result, "answer", None),
                    "meta": getattr(result, "meta", None),
                    "attempts": attempts,
                }
            )
            subtask.status = final_status
            executed.append(subtask)

        return executed

    def _execute_with_retry(
        self,
        subtask: Task,
    ) -> tuple[object | None, EvaluationResult | None, int]:
        """Execute a subtask with optional validation and retry policy."""

        attempt = 1
        last_result: object | None = None
        last_evaluation: EvaluationResult | None = None

        while True:
            last_result = self.router.run(subtask)

            if not self.validator:
                return last_result, None, attempt

            last_evaluation = self.validator(last_result)
            decision = self.retry_policy.decide(last_evaluation, attempt=attempt)
            logger.info(
                "Evaluation for task %s attempt=%d ok=%s should_retry=%s reason=%s",
                subtask.id,
                attempt,
                last_evaluation.ok,
                decision.should_retry,
                decision.reason,
            )

            if not decision.should_retry:
                return last_result, last_evaluation, attempt

            attempt += 1
