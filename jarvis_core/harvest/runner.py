"""Runners for `jarvis harvest watch` and `jarvis harvest work`."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.bundle import BundleAssembler
from jarvis_core.network.degradation import DegradationLevel, get_degradation_manager

from .budget import parse_budget
from .pubmed_watch import watch_pubmed
from .queue import HarvestQueue
from .worker import process_queue


def run_watch(
    *,
    source: str,
    since_hours: int,
    budget_raw: str,
    out: str,
    out_run: str,
    query: str,
) -> dict:
    run_id = _resolve_run_id(out_run)
    run_dir = Path(out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    harvest_dir = run_dir / "harvest"
    harvest_dir.mkdir(parents=True, exist_ok=True)
    queue = HarvestQueue(harvest_dir / "queue.jsonl")
    assembler = BundleAssembler(run_dir)

    budget = parse_budget(budget_raw)
    warnings: list[dict] = []
    fail_reasons: list[dict] = []
    discovered: list[dict] = []

    offline = _is_offline()
    if offline:
        fail_reasons.append(
            {"code": "OFFLINE_MODE", "msg": "watch skipped in offline mode", "severity": "warning"}
        )
    elif source != "pubmed":
        fail_reasons.append(
            {"code": "INPUT_INVALID", "msg": f"unsupported source: {source}", "severity": "error"}
        )
    else:
        discovered, watch_warnings = watch_pubmed(
            since_hours=since_hours,
            max_items=budget.max_items,
            query=query,
        )
        warnings.extend(watch_warnings)

    added = queue.enqueue_many(discovered) if discovered else 0
    stats = {
        "mode": "watch",
        "source": source,
        "discovered": len(discovered),
        "queued_added": added,
        "queue_total": len(queue.load()),
        "budget": {
            "max_items": budget.max_items,
            "max_minutes": budget.max_minutes,
            "max_requests": budget.max_requests,
        },
    }
    (harvest_dir / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_harvest_report(run_dir=run_dir, mode="watch", stats=stats, fail_reasons=fail_reasons)

    gate_passed = added > 0 and not _has_fatal(fail_reasons)
    if not gate_passed and not fail_reasons:
        fail_reasons.append(
            {"code": "WATCH_EMPTY", "msg": "No new queue items were added.", "severity": "warning"}
        )
    artifacts = {
        "papers": [
            {"paper_id": item.get("paper_key"), "title": item.get("title", ""), "year": 0}
            for item in discovered
        ],
        "claims": [],
        "evidence": [],
        "scores": {"features": {"queued_added": added}, "rankings": []},
        "answer": f"Harvest watch completed. Added {added} items to queue.",
        "citations": [],
        "warnings": warnings,
    }
    assembler.build(
        _context(run_id=run_id, goal="harvest watch", pipeline="harvest.watch"),
        artifacts,
        quality_report={"gate_passed": gate_passed, "fail_reasons": fail_reasons},
    )
    return _load_result(run_dir, run_id)


def run_work(*, budget_raw: str, out: str, out_run: str, oa_only: bool) -> dict:
    run_id = _resolve_run_id(out_run)
    run_dir = Path(out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    harvest_dir = run_dir / "harvest"
    harvest_dir.mkdir(parents=True, exist_ok=True)
    assembler = BundleAssembler(run_dir)

    budget = parse_budget(budget_raw)
    warnings: list[dict] = []
    fail_reasons: list[dict] = []
    stats = process_queue(run_dir=run_dir, budget=budget, oa_only=oa_only)
    if stats["budget"]["exceeded"]:
        fail_reasons.append(
            {
                "code": "BUDGET_EXCEEDED",
                "msg": "Harvest work stopped because budget was reached.",
                "severity": "warning",
            }
        )
    if stats["processed"] == 0:
        fail_reasons.append(
            {
                "code": "QUEUE_NOT_CONSUMED",
                "msg": "No queued items were processed.",
                "severity": "warning",
            }
        )
    (harvest_dir / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_harvest_report(run_dir=run_dir, mode="work", stats=stats, fail_reasons=fail_reasons)

    gate_passed = (
        stats["processed"] > 0 and not _has_fatal(fail_reasons) and not stats["budget"]["exceeded"]
    )
    artifacts = {
        "papers": [],
        "claims": [],
        "evidence": [],
        "scores": {"features": {"processed": stats["processed"]}, "rankings": []},
        "answer": f"Harvest work completed. Processed={stats['processed']} skipped={stats['skipped']}.",
        "citations": [],
        "warnings": warnings,
    }
    assembler.build(
        _context(run_id=run_id, goal="harvest work", pipeline="harvest.work"),
        artifacts,
        quality_report={"gate_passed": gate_passed, "fail_reasons": fail_reasons},
    )
    return _load_result(run_dir, run_id)


def _write_harvest_report(run_dir: Path, mode: str, stats: dict, fail_reasons: list[dict]) -> None:
    report_path = run_dir / "harvest" / "report.md"
    lines = [
        "# Harvest Report",
        "",
        f"- Mode: {mode}",
        f"- Queue persistence scope: run-scoped (run_id={run_dir.name})",
        f"- Queue path: logs/runs/{run_dir.name}/harvest/queue.jsonl",
        "",
        "## Stats",
    ]
    for key, value in stats.items():
        lines.append(f"- {key}: {value}")
    if fail_reasons:
        lines.extend(["", "## Notes"])
        for reason in fail_reasons:
            lines.append(f"- [{reason.get('code', 'WARN')}] {reason.get('msg', '')}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _resolve_run_id(out_run: str) -> str:
    if out_run and out_run != "auto":
        return out_run
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{now}_{uuid.uuid4().hex[:8]}"


def _context(*, run_id: str, goal: str, pipeline: str) -> dict:
    return {
        "run_id": run_id,
        "task_id": run_id,
        "goal": goal,
        "query": goal,
        "pipeline": pipeline,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": 42,
        "model": "feature-runner",
    }


def _is_offline() -> bool:
    return get_degradation_manager().get_level() == DegradationLevel.OFFLINE


def _has_fatal(fail_reasons: list[dict]) -> bool:
    return any(
        str(reason.get("code", "")).upper() in BundleAssembler.FATAL_FAIL_CODES
        for reason in fail_reasons
    )


def _load_result(run_dir: Path, run_id: str) -> dict:
    result_path = run_dir / "result.json"
    status = "needs_retry"
    if result_path.exists():
        try:
            status = str(
                json.loads(result_path.read_text(encoding="utf-8")).get("status", "needs_retry")
            )
        except Exception:
            status = "needs_retry"
    return {"run_id": run_id, "run_dir": str(run_dir), "status": status}
