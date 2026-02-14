"""Weekly scoreboard for ops_extract quality tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


@dataclass
class ScoreboardResult:
    ops_score: float
    extract_score: float
    run_count: int
    anomalies: list[str]
    window_start: str
    window_end: str


def _collect_runs(base_dir: Path, *, days: int = 7) -> list[Path]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(1, int(days)))
    runs: list[Path] = []
    if not base_dir.exists():
        return runs
    for run_dir in sorted(base_dir.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("_"):
            continue
        meta = _read_json(run_dir / "run_metadata.json")
        finished_at = _parse_time(str(meta.get("finished_at", "")))
        if finished_at is None:
            continue
        if finished_at >= start:
            runs.append(run_dir)
    return runs


def compute_ops_score(runs: list[Path]) -> float:
    if not runs:
        return 100.0
    committed = 0
    contract_failures = 0
    sync_failures = 0
    duplicate_risks = 0
    for run_dir in runs:
        manifest = _read_json(run_dir / "manifest.json")
        warnings_payload = _read_json(run_dir / "warnings.json")
        sync_state = _read_json(run_dir / "sync_state.json")
        if bool(manifest.get("committed_drive", False)):
            committed += 1
        warnings = warnings_payload.get("warnings", [])
        if isinstance(warnings, list):
            for warning in warnings:
                code = str((warning or {}).get("code", ""))
                if code == "CONTRACT_VALIDATION_FAILED":
                    contract_failures += 1
                if code in {"SYNC_FAILED", "SYNC_DEFERRED"}:
                    sync_failures += 1
        if str(sync_state.get("state", "")) == "deferred":
            duplicate_risks += 1
    total = len(runs)
    committed_rate = committed / total
    penalty = (contract_failures * 3 + sync_failures * 2 + duplicate_risks) / max(1, total)
    return max(0.0, min(100.0, round(committed_rate * 100 - penalty * 10, 2)))


def compute_extract_score(runs: list[Path]) -> float:
    if not runs:
        return 100.0
    total_chars = 0
    ocr_failures = 0
    empty_ratio_sum = 0.0
    for run_dir in runs:
        metrics = _read_json(run_dir / "metrics.json")
        extract = metrics.get("extract", {}) if isinstance(metrics, dict) else {}
        total_chars += int(extract.get("total_chars", 0) or 0)
        empty_ratio_sum += float(extract.get("empty_page_ratio", 0.0) or 0.0)
        warnings_payload = _read_json(run_dir / "warnings.json")
        warnings = warnings_payload.get("warnings", [])
        if isinstance(warnings, list) and any((w or {}).get("code") == "OCR_ERROR" for w in warnings):
            ocr_failures += 1
    total = len(runs)
    mean_chars = total_chars / max(1, total)
    mean_empty_ratio = empty_ratio_sum / max(1, total)
    score = 100.0
    if mean_chars < 500:
        score -= 20.0
    score -= mean_empty_ratio * 30.0
    score -= (ocr_failures / max(1, total)) * 30.0
    return max(0.0, min(100.0, round(score, 2)))


def detect_anomalies(*, runs: list[Path], ops_score: float, extract_score: float) -> list[str]:
    anomalies: list[str] = []
    if ops_score < 85:
        anomalies.append("OPS_SCORE_BELOW_85")
    if extract_score < 85:
        anomalies.append("EXTRACT_SCORE_BELOW_85")
    if len(runs) == 0:
        anomalies.append("NO_RUNS_IN_WINDOW")
    return anomalies


def generate_weekly_report(
    *,
    runs_base: Path = Path("logs/runs"),
    reports_base: Path = Path("reports/weekly"),
    days: int = 7,
) -> ScoreboardResult:
    now = datetime.now(timezone.utc)
    runs = _collect_runs(runs_base, days=days)
    ops_score = compute_ops_score(runs)
    extract_score = compute_extract_score(runs)
    anomalies = detect_anomalies(runs=runs, ops_score=ops_score, extract_score=extract_score)
    year, week, _ = now.isocalendar()
    out_dir = reports_base / f"{year}-W{week:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ops_score": ops_score,
        "extract_score": extract_score,
        "run_count": len(runs),
        "anomalies": anomalies,
        "window_start": (now - timedelta(days=days)).isoformat(),
        "window_end": now.isoformat(),
    }
    with open(out_dir / "scoreboard.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(out_dir / "scoreboard.md", "w", encoding="utf-8") as f:
        f.write("# Ops/Extract Weekly Scoreboard\n\n")
        f.write(f"- ops_score: {ops_score}\n")
        f.write(f"- extract_score: {extract_score}\n")
        f.write(f"- run_count: {len(runs)}\n")
        f.write(f"- anomalies: {', '.join(anomalies) if anomalies else '(none)'}\n")
    with open(out_dir / "alerts.md", "w", encoding="utf-8") as f:
        if anomalies:
            f.write("# Alerts\n\n")
            for item in anomalies:
                f.write(f"- {item}\n")
        else:
            f.write("# Alerts\n\n- none\n")
    return ScoreboardResult(
        ops_score=ops_score,
        extract_score=extract_score,
        run_count=len(runs),
        anomalies=anomalies,
        window_start=payload["window_start"],
        window_end=payload["window_end"],
    )

