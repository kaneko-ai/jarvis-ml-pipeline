"""KPI Reporter.

Per RP-163, generates KPI reports from run history.
"""

from __future__ import annotations

import json
import csv
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class KPISnapshot:
    """A KPI snapshot at a point in time."""

    timestamp: str
    total_runs: int
    success_rate: float
    partial_rate: float
    failed_rate: float
    avg_duration_seconds: float
    avg_claims_per_run: float
    avg_citations_per_claim: float


def compute_kpis(
    runs: List[dict],
    timestamp: Optional[str] = None,
) -> KPISnapshot:
    """Compute KPIs from run records.

    Args:
        runs: List of run dicts with status, duration, claims, citations.
        timestamp: Snapshot timestamp (default: now).

    Returns:
        KPISnapshot with computed metrics.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat() + "Z"

    total = len(runs)
    if total == 0:
        return KPISnapshot(
            timestamp=timestamp,
            total_runs=0,
            success_rate=0.0,
            partial_rate=0.0,
            failed_rate=0.0,
            avg_duration_seconds=0.0,
            avg_claims_per_run=0.0,
            avg_citations_per_claim=0.0,
        )

    success = sum(1 for r in runs if r.get("status") == "success")
    partial = sum(1 for r in runs if r.get("status") == "partial")
    failed = total - success - partial

    durations = [r.get("duration_seconds", 0) for r in runs]
    claims = [r.get("claims_count", 0) for r in runs]
    citations = [r.get("citations_count", 0) for r in runs]

    total_claims = sum(claims)
    total_citations = sum(citations)

    return KPISnapshot(
        timestamp=timestamp,
        total_runs=total,
        success_rate=success / total,
        partial_rate=partial / total,
        failed_rate=failed / total,
        avg_duration_seconds=sum(durations) / total if durations else 0,
        avg_claims_per_run=total_claims / total,
        avg_citations_per_claim=total_citations / total_claims if total_claims > 0 else 0,
    )


def save_kpi_json(snapshot: KPISnapshot, output_path: str) -> None:
    """Save KPI snapshot as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": snapshot.timestamp,
                "total_runs": snapshot.total_runs,
                "success_rate": round(snapshot.success_rate, 4),
                "partial_rate": round(snapshot.partial_rate, 4),
                "failed_rate": round(snapshot.failed_rate, 4),
                "avg_duration_seconds": round(snapshot.avg_duration_seconds, 2),
                "avg_claims_per_run": round(snapshot.avg_claims_per_run, 2),
                "avg_citations_per_claim": round(snapshot.avg_citations_per_claim, 2),
            },
            f,
            indent=2,
        )


def save_kpi_csv(snapshots: List[KPISnapshot], output_path: str) -> None:
    """Save KPI history as CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "total_runs",
                "success_rate",
                "partial_rate",
                "failed_rate",
                "avg_duration",
                "avg_claims",
                "avg_citations",
            ]
        )
        for s in snapshots:
            writer.writerow(
                [
                    s.timestamp,
                    s.total_runs,
                    round(s.success_rate, 4),
                    round(s.partial_rate, 4),
                    round(s.failed_rate, 4),
                    round(s.avg_duration_seconds, 2),
                    round(s.avg_claims_per_run, 2),
                    round(s.avg_citations_per_claim, 2),
                ]
            )


def format_kpi_report(snapshot: KPISnapshot) -> str:
    """Format KPI snapshot as text."""
    return f"""KPI Report - {snapshot.timestamp}
{'=' * 40}

Runs:        {snapshot.total_runs}
Success:     {snapshot.success_rate:.1%}
Partial:     {snapshot.partial_rate:.1%}
Failed:      {snapshot.failed_rate:.1%}

Avg Duration:  {snapshot.avg_duration_seconds:.1f}s
Avg Claims:    {snapshot.avg_claims_per_run:.1f}
Avg Citations: {snapshot.avg_citations_per_claim:.1f}
"""
