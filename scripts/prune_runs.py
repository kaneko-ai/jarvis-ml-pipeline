"""Prune old run directories under public/runs.

Retention policy defaults:
- KEEP_DAYS=14
- KEEP_LAST=50

If both are specified, the stricter retention applies (must satisfy both).
Before deleting a run directory, append minimal manifest info to
public/runs/archive_index.jsonl for auditability.
"""
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


DEFAULT_KEEP_DAYS = 14
DEFAULT_KEEP_LAST = 50


@dataclass
class RunInfo:
    run_id: str
    path: Path
    created_at: Optional[datetime]
    sort_key: datetime
    manifest: dict


def parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def load_manifest(run_path: Path) -> dict:
    manifest_file = run_path / "manifest.json"
    if not manifest_file.exists():
        return {}
    try:
        with manifest_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[prune_runs] WARNING: Failed to load {manifest_file}: {exc}", file=sys.stderr)
        return {}


def build_run_info(run_path: Path) -> RunInfo:
    manifest = load_manifest(run_path)
    run_id = manifest.get("run_id") or run_path.name
    created_at = parse_iso_datetime(manifest.get("created_at", ""))

    if created_at is None:
        stat = run_path.stat()
        created_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

    return RunInfo(
        run_id=run_id,
        path=run_path,
        created_at=created_at,
        sort_key=created_at,
        manifest=manifest,
    )


def minimal_archive_entry(run_info: RunInfo, archived_at: datetime, reason: str) -> dict:
    quality = run_info.manifest.get("quality", {}) if run_info.manifest else {}
    return {
        "run_id": run_info.run_id,
        "created_at": run_info.manifest.get("created_at") or run_info.created_at.isoformat(),
        "status": run_info.manifest.get("status"),
        "papers_found": quality.get("papers_found"),
        "gate_passed": quality.get("gate_passed"),
        "archived_at": archived_at.isoformat(),
        "reason": reason,
    }


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def parse_int(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        print(f"[prune_runs] WARNING: invalid int value '{value}', using default {default}")
        return default


def main() -> int:
    keep_days = parse_int(os.environ.get("KEEP_DAYS"), DEFAULT_KEEP_DAYS)
    keep_last = parse_int(os.environ.get("KEEP_LAST"), DEFAULT_KEEP_LAST)

    runs_dir = Path("public") / "runs"
    if not runs_dir.exists():
        print(f"[prune_runs] runs directory not found: {runs_dir}")
        return 0

    run_paths = [p for p in runs_dir.iterdir() if p.is_dir()]
    run_infos = [build_run_info(run_path) for run_path in run_paths]

    if not run_infos:
        print("[prune_runs] no runs to prune")
        return 0

    run_infos.sort(key=lambda item: item.sort_key, reverse=True)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=keep_days)

    keep_by_days = {info.run_id for info in run_infos if info.created_at >= cutoff}
    keep_by_last = {info.run_id for info in run_infos[:keep_last]}

    apply_days = keep_days is not None
    apply_last = keep_last is not None

    if apply_days and apply_last:
        keep_ids = keep_by_days & keep_by_last
        reason = f"keep_days={keep_days}, keep_last={keep_last}"
    elif apply_days:
        keep_ids = keep_by_days
        reason = f"keep_days={keep_days}"
    else:
        keep_ids = keep_by_last
        reason = f"keep_last={keep_last}"

    archive_path = runs_dir / "archive_index.jsonl"
    archived_at = datetime.now(timezone.utc)

    delete_infos = [info for info in run_infos if info.run_id not in keep_ids]

    print(
        "[prune_runs] total=%d keep=%d delete=%d (%s)"
        % (len(run_infos), len(keep_ids), len(delete_infos), reason)
    )

    for info in delete_infos:
        entry = minimal_archive_entry(info, archived_at=archived_at, reason=reason)
        append_jsonl(archive_path, entry)
        shutil.rmtree(info.path)
        print(f"[prune_runs] deleted {info.path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
