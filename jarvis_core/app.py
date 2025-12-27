"""Application Core.

Per MASTER_SPEC v1.1, this is the ONLY entry point for task execution.
成果物契約: run_config.json, result.json, eval_summary.json, events.jsonl 必須
成功条件: gate_passed == true ⇔ status == "success"
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .task import Task, TaskCategory
from .run_config import RunConfig


class TelemetryMissingError(Exception):
    """Raised when telemetry was not generated (hard gate failure)."""
    pass


class ContractViolationError(Exception):
    """Raised when artifact contract is violated."""
    pass


@dataclass
class AppResult:
    """Result from app execution."""

    run_id: str
    log_dir: str  # Path to logs directory
    status: str  # success, failed, needs_retry
    answer: str
    citations: list
    warnings: list
    gate_passed: bool = False
    eval_result: Optional[dict] = None


def run_task(
    task_dict: Dict[str, Any],
    run_config_dict: Optional[Dict[str, Any]] = None,
) -> AppResult:
    """Execute a task through the unified pipeline.

    This is the ONLY entry point for task execution.
    CLI calls this function. Direct calls outside CLI are for testing only.

    HARD GATES (per MASTER_SPEC v1.1):
    1. events.jsonl MUST be generated
    2. result.json MUST be generated
    3. eval_summary.json MUST be generated
    4. status == "success" only if gate_passed == true

    Args:
        task_dict: Task specification with goal, category, etc.
        run_config_dict: Optional run configuration.

    Returns:
        AppResult with answer, metadata, and log_dir.

    Raises:
        TelemetryMissingError: If events.jsonl was not generated.
        ContractViolationError: If required artifacts are missing.
    """
    from .executor import ExecutionEngine
    from .llm import LLMClient
    from .planner import Planner
    from .router import Router
    from .evidence import EvidenceStore
    from .telemetry import init_logger
    from .storage import RunStore
    from .eval.quality_gate import QualityGateVerifier

    # Generate run_id
    run_id = str(uuid.uuid4())

    # Initialize config
    config = RunConfig.from_dict(run_config_dict) if run_config_dict else RunConfig()
    config.apply_seed()

    # === Use RunStore for all path decisions (per MASTER_SPEC) ===
    store = RunStore(run_id, base_dir="logs/runs")
    log_dir = store.run_dir

    # Initialize telemetry - MUST succeed
    logger = init_logger(run_id, logs_dir="logs/runs")
    assert logger is not None, "TelemetryLogger must be initialized"

    # Save config (artifact 1/4)
    store.save_config({
        "run_id": run_id,
        "seed": config.seed,
        "model": config.model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

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

    # Initialize verifier (per MASTER_SPEC: Verify強制)
    verifier = QualityGateVerifier(
        require_citations=True,
        require_locators=True,
    )

    # Execute with guaranteed artifact generation
    answer = ""
    citations: List[Dict[str, Any]] = []
    warnings: List[str] = []
    execution_error: Optional[str] = None

    try:
        subtasks = engine.run(task)

        # Extract result from last subtask
        for st in subtasks:
            if hasattr(st, "result") and st.result:
                result = st.result
                if hasattr(result, "answer"):
                    answer = result.answer
                if hasattr(result, "citations"):
                    citations = result.citations or []
                if hasattr(result, "meta") and result.meta:
                    warnings.extend(result.meta.get("warnings", []))

        # === RUN_END (mandatory event) ===
        logger.log_event(
            event="RUN_END",
            event_type="ACTION",
            trace_id=run_id,
            task_id=task_id,
            payload={"execution": "complete"},
        )

    except Exception as e:
        execution_error = str(e)
        warnings.append(f"Execution error: {execution_error}")

        # === RUN_ERROR (mandatory event) ===
        logger.log_event(
            event="RUN_ERROR",
            event_type="ACTION",
            trace_id=run_id,
            task_id=task_id,
            level="ERROR",
            payload={"error": execution_error, "error_type": type(e).__name__},
        )

    # === VERIFY (per MASTER_SPEC: Verify強制) ===
    logger.log_event(
        event="VERIFY_START",
        event_type="ACTION",
        trace_id=run_id,
        task_id=task_id,
        payload={},
    )

    verify_result = verifier.verify(
        answer=answer,
        citations=citations,
    )

    logger.log_event(
        event="VERIFY_END",
        event_type="ACTION",
        trace_id=run_id,
        task_id=task_id,
        payload={
            "gate_passed": verify_result.gate_passed,
            "fail_count": len(verify_result.fail_reasons),
        },
    )

    # === Determine final status (per MASTER_SPEC: gate_passed必須) ===
    # status == "success" ⇔ gate_passed == true AND no execution error
    if execution_error:
        final_status = "failed"
    elif verify_result.gate_passed:
        final_status = "success"
    else:
        # gate_passed == false → cannot be success
        final_status = "failed"

    # === Save result.json (artifact 2/4) ===
    result_data = {
        "run_id": run_id,
        "task_id": task_id,
        "status": final_status,
        "answer": answer,
        "citations": citations,
        "warnings": warnings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    store.save_result(result_data)

    # === Save eval_summary.json (artifact 3/4) ===
    eval_data = verify_result.to_eval_summary(run_id)
    eval_data["timestamp"] = datetime.now(timezone.utc).isoformat()
    store.save_eval(eval_data)

    # === HARD GATE 1: Verify telemetry was written (artifact 4/4) ===
    events_file = store.events_file
    if not events_file.exists() or events_file.stat().st_size == 0:
        raise TelemetryMissingError(
            f"Telemetry hard gate failed: events.jsonl not generated at {events_file}"
        )

    # === HARD GATE 2: Verify artifact contract ===
    missing = store.validate_contract()
    if missing:
        raise ContractViolationError(
            f"Artifact contract violated: missing files {missing}"
        )

    return AppResult(
        run_id=run_id,
        log_dir=str(log_dir),
        status=final_status,
        answer=answer,
        citations=citations,
        warnings=warnings,
        gate_passed=verify_result.gate_passed,
        eval_result=eval_data,
    )


