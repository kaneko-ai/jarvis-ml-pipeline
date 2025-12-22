"""Application Core.

Per RP-09/RP-18, this is the ONLY entry point for task execution.
Telemetry MUST be generated for every execution (hard gate).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .task import Task, TaskCategory
from .run_config import RunConfig


class TelemetryMissingError(Exception):
    """Raised when telemetry was not generated (hard gate failure)."""
    pass


@dataclass
class AppResult:
    """Result from app execution."""

    run_id: str
    log_dir: str  # Path to logs directory
    status: str  # complete, partial, failed
    answer: str
    citations: list
    warnings: list
    eval_result: Optional[dict] = None


def run_task(
    task_dict: Dict[str, Any],
    run_config_dict: Optional[Dict[str, Any]] = None,
) -> AppResult:
    """Execute a task through the unified pipeline.

    This is the ONLY entry point for task execution.
    CLI, Web, and run_jarvis() all call this function.

    HARD GATE: events.jsonl MUST be generated or TelemetryMissingError is raised.

    Args:
        task_dict: Task specification with goal, category, etc.
        run_config_dict: Optional run configuration.

    Returns:
        AppResult with answer, metadata, and log_dir.

    Raises:
        TelemetryMissingError: If events.jsonl was not generated.
    """
    from .executor import ExecutionEngine
    from .llm import LLMClient
    from .planner import Planner
    from .router import Router
    from .evidence import EvidenceStore
    from .telemetry import init_logger

    # Generate run_id
    run_id = str(uuid.uuid4())

    # Initialize config
    config = RunConfig.from_dict(run_config_dict) if run_config_dict else RunConfig()
    config.apply_seed()

    # Determine log directory (absolute path for clarity)
    log_dir = Path("logs/runs") / run_id
    log_dir.mkdir(parents=True, exist_ok=True)

    # Initialize telemetry - MUST succeed
    logger = init_logger(run_id, logs_dir="logs/runs")
    assert logger is not None, "TelemetryLogger must be initialized"

    # Save config
    config.save(str(log_dir / "run_config.json"))

    # Parse task
    goal = task_dict.get("goal") or task_dict.get("user_goal", "")
    category = task_dict.get("category", "generic")

    try:
        task_category = TaskCategory(category)
    except ValueError:
        task_category = TaskCategory.GENERIC

    # Create task
    task_id = task_dict.get("task_id", str(uuid.uuid4()))
    task = Task(
        task_id=task_id,
        title=goal[:50] + "..." if len(goal) > 50 else goal,
        category=task_category,
        user_goal=goal,
        inputs=task_dict.get("inputs", {"query": goal}),
    )

    # === RUN_START (mandatory event) ===
    logger.log_event(
        event="RUN_START",
        event_type="ACTION",
        trace_id=run_id,
        task_id=task_id,
        payload={"goal": goal, "category": category},
    )

    # Initialize engine
    llm = LLMClient(model=config.model)
    router = Router(llm)
    planner = Planner()
    evidence_store = EvidenceStore()

    engine = ExecutionEngine(
        planner=planner,
        router=router,
        evidence_store=evidence_store,
    )

    # Execute with guaranteed RUN_END or RUN_ERROR
    try:
        subtasks = engine.run(task)

        # Extract result from last subtask
        answer = ""
        citations = []
        warnings = []
        status = "complete"

        for st in subtasks:
            if hasattr(st, "result") and st.result:
                result = st.result
                if hasattr(result, "answer"):
                    answer = result.answer
                if hasattr(result, "citations"):
                    citations = result.citations
                if hasattr(result, "meta") and result.meta:
                    warnings.extend(result.meta.get("warnings", []))

        # === RUN_END (mandatory event) ===
        logger.log_event(
            event="RUN_END",
            event_type="ACTION",
            trace_id=run_id,
            task_id=task_id,
            payload={"status": status},
        )

        app_result = AppResult(
            run_id=run_id,
            log_dir=str(log_dir),
            status=status,
            answer=answer,
            citations=citations,
            warnings=warnings,
        )

    except Exception as e:
        # === RUN_ERROR (mandatory event) ===
        logger.log_event(
            event="RUN_ERROR",
            event_type="ACTION",
            trace_id=run_id,
            task_id=task_id,
            level="ERROR",
            payload={"error": str(e), "error_type": type(e).__name__},
        )

        app_result = AppResult(
            run_id=run_id,
            log_dir=str(log_dir),
            status="failed",
            answer="",
            citations=[],
            warnings=[str(e)],
        )

    # === HARD GATE: Verify telemetry was written ===
    events_file = log_dir / "events.jsonl"
    if not events_file.exists() or events_file.stat().st_size == 0:
        raise TelemetryMissingError(
            f"Telemetry hard gate failed: events.jsonl not generated at {events_file}"
        )

    return app_result

