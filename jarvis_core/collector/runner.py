"""Runners for `jarvis collect papers` and `jarvis collect drive-sync`."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.bundle import BundleAssembler
from jarvis_core.network.degradation import DegradationLevel, get_degradation_manager

from .bibtex import to_bibtex
from .drive_sync import sync_to_drive
from .fetch import collect_papers


def run_collect_papers(
    *, query: str, max_items: int, oa_only: bool, out: str, out_run: str
) -> dict:
    run_id = _resolve_run_id(out_run)
    run_dir = Path(out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    collector_dir = run_dir / "collector"
    collector_dir.mkdir(parents=True, exist_ok=True)
    (collector_dir / "pdfs").mkdir(exist_ok=True)
    (collector_dir / "bibtex").mkdir(exist_ok=True)
    assembler = BundleAssembler(run_dir)

    fail_reasons: list[dict] = []
    warnings: list[dict] = []
    papers: list[dict] = []

    if _is_offline():
        fail_reasons.append(
            {
                "code": "OFFLINE_MODE",
                "msg": "Collector cannot access external sources in offline mode.",
                "severity": "warning",
            }
        )
    else:
        papers, collect_warnings = collect_papers(query=query, max_items=max_items, oa_only=oa_only)
        warnings.extend(collect_warnings)
    if not papers and not fail_reasons:
        fail_reasons.append(
            {
                "code": "COLLECT_EMPTY",
                "msg": "No papers collected for the query.",
                "severity": "warning",
            }
        )

    (collector_dir / "papers.json").write_text(
        json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for paper in papers:
        bib = to_bibtex(paper)
        bib_name = str(paper.get("paper_key", "unknown")).replace("/", "_")
        (collector_dir / "bibtex" / f"{bib_name}.bib").write_text(bib, encoding="utf-8")

    report_lines = [
        "# Collector Report",
        "",
        f"- Query: {query}",
        f"- OA only: {oa_only}",
        f"- Collected papers: {len(papers)}",
        "- PDF download: deferred (metadata/BibTeX stored first).",
    ]
    if fail_reasons:
        report_lines.extend(["", "## Notes"])
        for reason in fail_reasons:
            report_lines.append(f"- [{reason.get('code', 'WARN')}] {reason.get('msg', '')}")
    (collector_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    gate_passed = len(papers) > 0 and not _has_fatal(fail_reasons)
    artifacts = {
        "papers": [
            {"paper_id": p.get("paper_key"), "title": p.get("title", ""), "year": 0} for p in papers
        ],
        "claims": [],
        "evidence": [],
        "scores": {"features": {"paper_count": len(papers)}, "rankings": []},
        "answer": f"Collected {len(papers)} papers.",
        "citations": [],
        "warnings": warnings,
    }
    assembler.build(
        _context(run_id=run_id, goal="collect papers", pipeline="collector.papers"),
        artifacts,
        quality_report={"gate_passed": gate_passed, "fail_reasons": fail_reasons},
    )
    return _load_result(run_dir, run_id)


def run_drive_sync(*, run_id: str, out: str, drive_folder: str | None) -> dict:
    run_dir = Path(out) / run_id
    collector_dir = run_dir / "collector"
    collector_dir.mkdir(parents=True, exist_ok=True)
    ok, message = sync_to_drive(run_dir=run_dir, drive_folder=drive_folder)
    report_path = collector_dir / "report.md"
    base = (
        report_path.read_text(encoding="utf-8")
        if report_path.exists()
        else "# Collector Report\n\n"
    )
    suffix = [
        "",
        "## Drive Sync",
        f"- Result: {'success' if ok else 'human_action_required'}",
        f"- Message: {message}",
    ]
    report_path.write_text(base.rstrip() + "\n" + "\n".join(suffix) + "\n", encoding="utf-8")
    return {"run_id": run_id, "run_dir": str(run_dir), "status": "success" if ok else "needs_retry"}


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
