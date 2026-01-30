"""Run Summarizer.

Per RP-146, generates human-readable run summaries from telemetry.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    """Summary of a run."""

    run_id: str
    status: str
    total_steps: int
    failed_steps: int
    retry_count: int
    docs_fetched: int
    claims_generated: int
    citations_added: int
    duration_seconds: float
    top_failures: list[dict]
    warnings: list[str]


def summarize_events(events_path: str) -> RunSummary:
    """Summarize a run from its events.jsonl.

    Args:
        events_path: Path to events.jsonl.

    Returns:
        RunSummary with key metrics.
    """
    path = Path(events_path)
    if not path.exists():
        raise FileNotFoundError(f"Events file not found: {events_path}")

    events = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    # Extract metrics
    run_id = ""
    status = "unknown"
    steps = set()
    failed_steps = 0
    retry_count = 0
    docs_fetched = 0
    claims_generated = 0
    citations_added = 0
    start_time = None
    end_time = None
    failures = []
    warnings = []

    for event in events:
        action = event.get("action", "")
        run_id = event.get("run_id", run_id)

        if "step_id" in event:
            steps.add(event["step_id"])

        if action == "RUN_START":
            start_time = event.get("timestamp")
        elif action == "RUN_END":
            end_time = event.get("timestamp")
            status = event.get("status", "unknown")
        elif action == "RUN_ERROR":
            status = "failed"
            failures.append(
                {
                    "action": action,
                    "error": event.get("error_type", ""),
                    "message": event.get("message", "")[:100],
                }
            )
        elif action == "STEP_FAILED":
            failed_steps += 1
            failures.append(
                {
                    "step": event.get("step_id"),
                    "error": event.get("error", "")[:100],
                }
            )
        elif "RETRY" in action:
            retry_count += 1
        elif action == "FETCH_RESULT":
            if event.get("success"):
                docs_fetched += 1
        elif action == "CLAIM_GENERATED":
            claims_generated += 1
        elif action == "CITATION_ADDED":
            citations_added += 1
        elif "WARN" in action:
            warnings.append(event.get("message", "")[:50])

    # Calculate duration
    duration = 0.0
    if start_time and end_time:
        try:
            from datetime import datetime

            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            duration = (end - start).total_seconds()
        except Exception as e:
            logger.debug(f"Duration calculation failed for run {run_id}: {e}")

    return RunSummary(
        run_id=run_id,
        status=status,
        total_steps=len(steps),
        failed_steps=failed_steps,
        retry_count=retry_count,
        docs_fetched=docs_fetched,
        claims_generated=claims_generated,
        citations_added=citations_added,
        duration_seconds=duration,
        top_failures=failures[:5],
        warnings=warnings[:10],
    )


def format_summary(summary: RunSummary) -> str:
    """Format summary as human-readable text."""
    lines = [
        "=" * 50,
        f"Run Summary: {summary.run_id}",
        "=" * 50,
        "",
        f"Status:      {summary.status}",
        f"Duration:    {summary.duration_seconds:.1f}s",
        f"Steps:       {summary.total_steps} ({summary.failed_steps} failed)",
        f"Retries:     {summary.retry_count}",
        "",
        "--- Metrics ---",
        f"Docs Fetched:     {summary.docs_fetched}",
        f"Claims Generated: {summary.claims_generated}",
        f"Citations Added:  {summary.citations_added}",
    ]

    if summary.top_failures:
        lines.append("")
        lines.append("--- Top Failures ---")
        for f in summary.top_failures[:3]:
            lines.append(f"  - {f}")

    if summary.warnings:
        lines.append("")
        lines.append("--- Warnings ---")
        for w in summary.warnings[:5]:
            lines.append(f"  - {w}")

    return "\n".join(lines)
