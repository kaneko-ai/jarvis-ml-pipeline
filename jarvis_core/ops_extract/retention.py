"""Retention workflow for ops_extract runs."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .learning import lesson_exists_for_run, record_lesson


@dataclass
class OpsExtractRetentionResult:
    moved_to_trash: list[str]
    deleted_from_trash: list[str]
    kept: list[str]
    dry_run: bool = False


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def apply_ops_extract_retention(
    *,
    runs_base: Path = Path("logs/runs"),
    lessons_path: Path | None = None,
    now: datetime | None = None,
    failed_days: int = 30,
    success_days: int = 180,
    trash_days: int = 7,
    max_delete_per_run: int = 200,
    dry_run: bool = False,
    current_run_id: str | None = None,
) -> OpsExtractRetentionResult:
    now = now or datetime.now(timezone.utc)
    trash_dir = runs_base / "_trash_candidates"
    trash_dir.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    deleted: list[str] = []
    kept: list[str] = []

    for run_dir in runs_base.iterdir():
        if not run_dir.is_dir() or run_dir.name.startswith("_"):
            continue
        if current_run_id and run_dir.name == current_run_id:
            kept.append(run_dir.name)
            continue
        meta = _load_json(run_dir / "run_metadata.json")
        if meta.get("mode") != "ops_extract":
            kept.append(run_dir.name)
            continue

        manifest = _load_json(run_dir / "manifest.json")
        status = meta.get("status") or manifest.get("status")
        pinned = bool(
            manifest.get("pinned", False)
            or meta.get("pinned", False)
            or (run_dir / ".pin").exists()
        )
        finished_at = _parse_time(meta.get("finished_at")) or _parse_time(
            manifest.get("finished_at")
        )
        if finished_at is None:
            kept.append(run_dir.name)
            continue
        age = now - finished_at

        if status == "failed" and age.days >= failed_days:
            if not (run_dir / "failure_analysis.json").exists():
                kept.append(run_dir.name)
                continue
            if not lesson_exists_for_run(run_dir.name, lessons_path=lessons_path):
                failure = _load_json(run_dir / "failure_analysis.json")
                try:
                    if not dry_run:
                        record_lesson(
                            run_id=run_dir.name,
                            category=str(failure.get("category", "unknown")),
                            root_cause=str(failure.get("root_cause_guess", "")),
                            recommendation_steps=list(failure.get("recommendation_steps", [])),
                            preventive_checks=list(failure.get("preventive_checks", [])),
                            lessons_path=lessons_path,
                        )
                except Exception:
                    kept.append(run_dir.name)
                    continue
            if not dry_run:
                shutil.move(str(run_dir), str(trash_dir / run_dir.name))
            moved.append(run_dir.name)
            continue

        if status == "success" and age.days >= success_days and not pinned:
            if not dry_run:
                shutil.move(str(run_dir), str(trash_dir / run_dir.name))
            moved.append(run_dir.name)
            continue

        kept.append(run_dir.name)

    delete_count = 0
    for cand in sorted(trash_dir.iterdir(), key=lambda p: p.name):
        if not cand.is_dir():
            continue
        if delete_count >= max(0, int(max_delete_per_run)):
            break
        mtime = datetime.fromtimestamp(cand.stat().st_mtime, tz=timezone.utc)
        if now - mtime >= timedelta(days=trash_days):
            if not dry_run:
                shutil.rmtree(cand, ignore_errors=True)
            deleted.append(cand.name)
            delete_count += 1

    return OpsExtractRetentionResult(
        moved_to_trash=sorted(moved),
        deleted_from_trash=sorted(deleted),
        kept=sorted(kept),
        dry_run=dry_run,
    )
