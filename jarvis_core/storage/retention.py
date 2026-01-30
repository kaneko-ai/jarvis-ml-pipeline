"""Storage Retention Policy.

Per PR-76, manages automatic cleanup of old runs.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RetentionPolicy:
    """Retention policy for run storage."""

    max_age_days: int = 30
    max_size_gb: float = 10.0
    keep_important: bool = True
    keep_latest_n: int = 10


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""

    deleted_runs: list[str]
    deleted_size_bytes: int
    kept_runs: int
    errors: list[str]


def get_run_age(run_dir: Path) -> timedelta | None:
    """Get age of a run from its events.jsonl."""
    events_file = run_dir / "events.jsonl"
    if not events_file.exists():
        return None

    try:
        with open(events_file, encoding="utf-8") as f:
            first_line = f.readline()
        if first_line:
            event = json.loads(first_line)
            ts = event.get("ts", "")
            if ts:
                run_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return datetime.now(run_time.tzinfo) - run_time
    except Exception as e:
        logger.debug(f"Failed to parse age for run {run_dir}: {e}")

    # Fallback to file mtime
    return timedelta(seconds=datetime.now().timestamp() - events_file.stat().st_mtime)


def get_run_size(run_dir: Path) -> int:
    """Get total size of a run directory."""
    total = 0
    for f in run_dir.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def is_important_run(run_dir: Path) -> bool:
    """Check if a run is marked as important."""
    important_file = run_dir / ".important"
    return important_file.exists()


def apply_retention_policy(
    runs_dir: str,
    policy: RetentionPolicy | None = None,
    dry_run: bool = False,
) -> CleanupResult:
    """Apply retention policy to runs directory."""
    if policy is None:
        policy = RetentionPolicy()

    runs_path = Path(runs_dir)
    if not runs_path.exists():
        return CleanupResult([], 0, 0, [])

    # Get all runs sorted by age (oldest first)
    runs = []
    for run_dir in runs_path.iterdir():
        if run_dir.is_dir():
            age = get_run_age(run_dir)
            size = get_run_size(run_dir)
            important = is_important_run(run_dir)
            runs.append((run_dir, age, size, important))

    # Sort by age (oldest first, None ages at end)
    runs.sort(key=lambda x: x[1] or timedelta(days=0))

    deleted = []
    deleted_bytes = 0
    errors = []
    total_size = sum(r[2] for r in runs)

    # Keep at least N latest
    protected_count = policy.keep_latest_n

    for i, (run_dir, age, size, important) in enumerate(runs):
        should_delete = False
        reason = ""

        # Skip protected runs
        if i >= len(runs) - protected_count:
            continue

        # Check importance
        if policy.keep_important and important:
            continue

        # Check age
        if age and age.days > policy.max_age_days:
            should_delete = True
            reason = f"age {age.days}d > {policy.max_age_days}d"

        # Check total size
        if total_size > policy.max_size_gb * 1024 * 1024 * 1024:
            should_delete = True
            reason = "total size exceeded"

        if should_delete:
            if dry_run:
                deleted.append(f"{run_dir.name} (dry-run: {reason})")
            else:
                try:
                    shutil.rmtree(run_dir)
                    deleted.append(run_dir.name)
                    deleted_bytes += size
                    total_size -= size
                except Exception as e:
                    errors.append(f"{run_dir.name}: {e}")

    kept = len(runs) - len(deleted)
    return CleanupResult(deleted, deleted_bytes, kept, errors)