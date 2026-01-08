"""Web Dashboard API.

Per RP-385, provides API endpoints for web dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class DashboardStats:
    """Dashboard statistics."""

    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_latency_ms: float
    papers_indexed: int
    last_updated: str


@dataclass
class RunSummary:
    """Summary of a run."""

    run_id: str
    query: str
    status: str
    created_at: str
    duration_seconds: float
    claim_count: int
    citation_count: int


class DashboardAPI:
    """API for web dashboard.

    Per RP-385:
    - React/Next.js frontend support
    - Run history listing
    - Result visualization
    """

    def __init__(
        self,
        runs_dir: str = "logs/runs",
    ):
        self.runs_dir = runs_dir
        self._runs_cache: Dict[str, RunSummary] = {}

    def get_stats(self) -> DashboardStats:
        """Get dashboard statistics.

        Returns:
            DashboardStats.
        """
        runs = self.list_runs()

        if not runs:
            return DashboardStats(
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                avg_latency_ms=0,
                papers_indexed=0,
                last_updated=datetime.utcnow().isoformat() + "Z",
            )

        total = len(runs)
        successful = sum(1 for r in runs if r.status == "success")
        failed = sum(1 for r in runs if r.status == "failed")

        durations = [r.duration_seconds for r in runs if r.duration_seconds > 0]
        avg_latency = (sum(durations) / len(durations) * 1000) if durations else 0

        return DashboardStats(
            total_runs=total,
            successful_runs=successful,
            failed_runs=failed,
            avg_latency_ms=avg_latency,
            papers_indexed=1000,  # Placeholder
            last_updated=datetime.utcnow().isoformat() + "Z",
        )

    def list_runs(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[RunSummary]:
        """List runs.

        Args:
            limit: Max results.
            offset: Pagination offset.
            status: Filter by status.

        Returns:
            List of run summaries.
        """
        from pathlib import Path

        runs_path = Path(self.runs_dir)
        if not runs_path.exists():
            return []

        runs = []
        for run_dir in runs_path.iterdir():
            if run_dir.is_dir():
                summary = self._load_run_summary(run_dir)
                if summary:
                    if status is None or summary.status == status:
                        runs.append(summary)

        # Sort by created_at descending
        runs.sort(key=lambda r: r.created_at, reverse=True)

        return runs[offset : offset + limit]

    def _load_run_summary(self, run_dir) -> Optional[RunSummary]:
        """Load run summary from directory."""
        summary_path = run_dir / "summary.json"

        if summary_path.exists():
            try:
                with open(summary_path) as f:
                    data = json.load(f)
                    return RunSummary(
                        run_id=data.get("run_id", run_dir.name),
                        query=data.get("query", ""),
                        status=data.get("status", "unknown"),
                        created_at=data.get("created_at", ""),
                        duration_seconds=data.get("duration_seconds", 0),
                        claim_count=data.get("claim_count", 0),
                        citation_count=data.get("citation_count", 0),
                    )
            except Exception:
                pass

        # Fallback: create summary from directory name
        return RunSummary(
            run_id=run_dir.name,
            query="",
            status="unknown",
            created_at="",
            duration_seconds=0,
            claim_count=0,
            citation_count=0,
        )

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get full run details.

        Args:
            run_id: Run ID.

        Returns:
            Full run data.
        """
        from pathlib import Path

        run_path = Path(self.runs_dir) / run_id

        if not run_path.exists():
            return None

        result = {"run_id": run_id}

        # Load output
        output_path = run_path / "output.json"
        if output_path.exists():
            with open(output_path) as f:
                result["output"] = json.load(f)

        # Load claims
        claims_path = run_path / "claims.json"
        if claims_path.exists():
            with open(claims_path) as f:
                result["claims"] = json.load(f)

        # Load events
        events_path = run_path / "events.jsonl"
        if events_path.exists():
            events = []
            with open(events_path) as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
            result["events"] = events

        return result

    def get_metrics_history(
        self,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get metrics history.

        Args:
            days: Number of days.

        Returns:
            Daily metrics.
        """
        # Placeholder - would aggregate from runs
        history = []
        for i in range(days):
            history.append(
                {
                    "date": f"2024-12-{22 - i:02d}",
                    "success_rate": 0.8 + (i % 5) * 0.02,
                    "avg_latency_ms": 1000 + i * 10,
                }
            )

        return history
