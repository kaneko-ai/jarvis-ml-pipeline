"""Telemetry Analyzer.

Per PR-69, provides failure analysis and step statistics.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StepStats:
    """Statistics for a step type."""

    step_type: str
    count: int = 0
    success_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    total_duration_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.count if self.count > 0 else 0.0

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.count if self.count > 0 else 0.0


@dataclass
class FailureRecord:
    """A recorded failure."""

    event: str
    error_type: str
    error_message: str
    step_id: int | None = None
    tool: str | None = None


@dataclass
class RunAnalysis:
    """Analysis of a run's events."""

    run_id: str
    total_events: int
    step_stats: dict[str, StepStats]
    top_failures: list[FailureRecord]
    timeline: list[str]


def analyze_events(events_file: Path) -> RunAnalysis:
    """Analyze events from a JSONL file."""
    events = []
    with open(events_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    run_id = events[0].get("run_id", "unknown") if events else "unknown"

    # Step stats
    stats: dict[str, StepStats] = defaultdict(lambda: StepStats(step_type=""))
    failures: list[FailureRecord] = []
    timeline: list[str] = []

    for event in events:
        evt = event.get("event", "")
        evt_type = event.get("event_type", "")
        level = event.get("level", "INFO")
        tool = event.get("tool", "")
        step_id = event.get("step_id")

        # Update timeline
        ts = event.get("ts", "")[:19]
        timeline.append(f"{ts} {evt}")

        # Track step stats by event type
        if evt_type not in stats:
            stats[evt_type] = StepStats(step_type=evt_type)
        stats[evt_type].count += 1

        if level == "ERROR":
            stats[evt_type].error_count += 1
            payload = event.get("payload", {})
            failures.append(FailureRecord(
                event=evt,
                error_type=payload.get("error_type", "Unknown"),
                error_message=payload.get("error", "")[:100],
                step_id=step_id,
                tool=tool,
            ))
        else:
            stats[evt_type].success_count += 1

    # Sort failures by frequency
    failure_counts: dict[str, int] = defaultdict(int)
    for f in failures:
        key = f"{f.event}:{f.error_type}"
        failure_counts[key] += 1

    top_failures = sorted(failures, key=lambda f: failure_counts[f"{f.event}:{f.error_type}"], reverse=True)[:10]

    return RunAnalysis(
        run_id=run_id,
        total_events=len(events),
        step_stats=dict(stats),
        top_failures=top_failures,
        timeline=timeline[:50],  # First 50 events
    )


def print_analysis(analysis: RunAnalysis) -> None:
    """Print analysis in human-readable format."""
    print(f"=== Run Analysis: {analysis.run_id} ===")
    print(f"Total events: {analysis.total_events}")
    print()

    print("Step Statistics:")
    for step_type, stats in sorted(analysis.step_stats.items()):
        print(f"  {step_type}: {stats.count} events, "
              f"{stats.success_rate:.0%} success, "
              f"{stats.error_count} errors")

    if analysis.top_failures:
        print()
        print("Top Failures:")
        for i, failure in enumerate(analysis.top_failures[:5], 1):
            print(f"  {i}. {failure.event}: {failure.error_type}")
            print(f"     {failure.error_message[:60]}...")
