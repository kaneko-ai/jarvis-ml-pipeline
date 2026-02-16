"""Runner for `jarvis radar run`."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.bundle import BundleAssembler
from jarvis_core.network.degradation import DegradationLevel, get_degradation_manager

from .analyzer import classify_findings
from .proposer import build_proposals, proposals_markdown
from .sources import collect_findings


def run_radar(
    *,
    source: str,
    query: str,
    since_days: int,
    out: str,
    out_run: str,
    rss_url: str | None = None,
    manual_urls_path: str | None = None,
) -> dict:
    run_id = _resolve_run_id(out_run)
    run_dir = Path(out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    radar_dir = run_dir / "radar"
    radar_dir.mkdir(parents=True, exist_ok=True)
    assembler = BundleAssembler(run_dir)

    fail_reasons: list[dict] = []
    warnings: list[dict] = []
    findings: list[dict] = []
    proposals: list[dict] = []

    if _is_offline():
        fail_reasons.append(
            {
                "code": "OFFLINE_MODE",
                "msg": "Radar sources are unavailable in offline mode.",
                "severity": "warning",
            }
        )
    else:
        findings, source_warnings = collect_findings(
            source=source,
            query=query,
            since_days=since_days,
            rss_url=rss_url,
            manual_urls_path=manual_urls_path,
        )
        warnings.extend(source_warnings)
        findings = classify_findings(findings)
        proposals = build_proposals(findings)
        if not findings:
            fail_reasons.append(
                {"code": "RADAR_EMPTY", "msg": "No findings were collected.", "severity": "warning"}
            )

    (radar_dir / "radar_findings.json").write_text(
        json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (radar_dir / "upgrade_proposals.md").write_text(proposals_markdown(proposals), encoding="utf-8")

    gate_passed = len(findings) > 0 and not _has_fatal(fail_reasons)
    artifacts = {
        "papers": [
            {"paper_id": item.get("id"), "title": item.get("title", ""), "year": 0}
            for item in findings
        ],
        "claims": [],
        "evidence": [],
        "scores": {"features": {"finding_count": len(findings)}, "rankings": []},
        "answer": f"Radar run completed with {len(findings)} findings and {len(proposals)} proposals.",
        "citations": [],
        "warnings": warnings,
    }
    assembler.build(
        _context(run_id=run_id, goal="radar run", pipeline="radar.run"),
        artifacts,
        quality_report={"gate_passed": gate_passed, "fail_reasons": fail_reasons},
    )
    return _load_result(run_dir, run_id)


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
