"""Task Graph.

Per V4.2 Sprint 2, this provides DAG-based task execution with dependency resolution.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskState(Enum):
    """Task execution state."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Cache hit


@dataclass
class TaskNode:
    """A node in the task graph."""

    task_id: str
    name: str
    fn: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: str | None = None
    cache_key: str | None = None

    def compute_cache_key(self, dep_results: dict[str, Any]) -> str:
        """Compute deterministic cache key."""
        # Include task name, args, and dependency results
        key_parts = [
            self.name,
            str(self.args),
            str(sorted(self.kwargs.items())),
        ]
        for dep_id in sorted(self.dependencies):
            if dep_id in dep_results:
                key_parts.append(f"{dep_id}:{hash(str(dep_results[dep_id]))}")

        content = "|".join(key_parts)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class TaskGraph:
    """DAG-based task execution with parallelization."""

    def __init__(self, max_workers: int = 4):
        self.nodes: dict[str, TaskNode] = {}
        self.max_workers = max_workers
        self.results: dict[str, Any] = {}
        self._cache: dict[str, Any] = {}

    def add_task(
        self,
        task_id: str,
        name: str,
        fn: Callable,
        args: tuple = (),
        kwargs: dict = None,
        dependencies: list[str] = None,
    ) -> TaskNode:
        """Add a task to the graph."""
        node = TaskNode(
            task_id=task_id,
            name=name,
            fn=fn,
            args=args,
            kwargs=kwargs or {},
            dependencies=dependencies or [],
        )
        self.nodes[task_id] = node
        return node

    def get_ready_tasks(self) -> list[str]:
        """Get tasks whose dependencies are all completed."""
        ready = []
        for task_id, node in self.nodes.items():
            if node.state != TaskState.PENDING:
                continue

            deps_met = all(
                self.nodes[dep].state in (TaskState.COMPLETED, TaskState.SKIPPED)
                for dep in node.dependencies
                if dep in self.nodes
            )

            if deps_met:
                ready.append(task_id)

        return ready

    def execute_task(self, task_id: str) -> Any:
        """Execute a single task."""
        from ..perf.trace_spans import end_span, start_span

        node = self.nodes[task_id]
        node.state = TaskState.RUNNING

        # Compute cache key
        dep_results = {d: self.results.get(d) for d in node.dependencies}
        cache_key = node.compute_cache_key(dep_results)
        node.cache_key = cache_key

        # Check cache
        if cache_key in self._cache:
            node.state = TaskState.SKIPPED
            node.result = self._cache[cache_key]
            self.results[task_id] = node.result
            return node.result

        # Execute with span tracking
        span_id = start_span(f"task:{node.name}", {"task_id": task_id})

        try:
            # Inject dependency results if function expects them
            if "dep_results" in node.kwargs:
                node.kwargs["dep_results"] = dep_results

            result = node.fn(*node.args, **node.kwargs)
            node.result = result
            node.state = TaskState.COMPLETED
            self.results[task_id] = result

            # Cache result
            self._cache[cache_key] = result

            end_span(span_id, item_count=1)
            return result

        except Exception as e:
            node.state = TaskState.FAILED
            node.error = str(e)
            end_span(span_id)
            raise

    def execute(self, parallel: bool = True) -> dict[str, Any]:
        """Execute all tasks respecting dependencies.

        Args:
            parallel: Whether to execute in parallel.

        Returns:
            Dict of task_id -> result.
        """
        if parallel and self.max_workers > 1:
            return self._execute_parallel()
        else:
            return self._execute_sequential()

    def _execute_sequential(self) -> dict[str, Any]:
        """Execute tasks sequentially."""
        while True:
            ready = self.get_ready_tasks()
            if not ready:
                break

            for task_id in ready:
                try:
                    self.execute_task(task_id)
                except Exception:
                    pass  # Continue with other tasks

        return self.results

    def _execute_parallel(self) -> dict[str, Any]:
        """Execute tasks in parallel."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                ready = self.get_ready_tasks()
                if not ready:
                    break

                futures = {
                    executor.submit(self.execute_task, task_id): task_id for task_id in ready
                }

                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass  # Continue with other tasks

        return self.results

    def set_cache(self, cache: dict[str, Any]) -> None:
        """Set external cache."""
        self._cache = cache

    def get_execution_order(self) -> list[str]:
        """Get topological order of tasks."""
        visited = set()
        order = []

        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            for dep in self.nodes[task_id].dependencies:
                if dep in self.nodes:
                    visit(dep)
            order.append(task_id)

        for task_id in self.nodes:
            visit(task_id)

        return order

    def get_stats(self) -> dict:
        """Get execution statistics."""
        stats = {
            "total": len(self.nodes),
            "completed": 0,
            "skipped": 0,
            "failed": 0,
            "pending": 0,
        }

        for node in self.nodes.values():
            if node.state == TaskState.COMPLETED:
                stats["completed"] += 1
            elif node.state == TaskState.SKIPPED:
                stats["skipped"] += 1
            elif node.state == TaskState.FAILED:
                stats["failed"] += 1
            else:
                stats["pending"] += 1

        return stats
