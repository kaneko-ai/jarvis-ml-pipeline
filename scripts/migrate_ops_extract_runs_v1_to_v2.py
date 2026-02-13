"""Migrate legacy ops_extract run artifacts from v1 layout to v2 contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jarvis_core.ops_extract.contracts import (
    OPS_EXTRACT_SCHEMA_VERSION,
    OPS_EXTRACT_SYNC_STATE_VERSION,
)
from jarvis_core.ops_extract.stage_cache import STAGE_CACHE_VERSION


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _write_json(path: Path, payload: dict[str, Any], *, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def migrate_run(run_dir: Path, *, dry_run: bool) -> bool:
    changed = False

    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        manifest = _read_json(manifest_path)
        if manifest:
            if not manifest.get("schema_version"):
                manifest["schema_version"] = OPS_EXTRACT_SCHEMA_VERSION
                changed = True
            if "committed_local" not in manifest:
                manifest["committed_local"] = bool(manifest.get("committed", True))
                changed = True
            if "committed_drive" not in manifest:
                manifest["committed_drive"] = False
                changed = True
            _write_json(manifest_path, manifest, dry_run=dry_run)

    sync_state_path = run_dir / "sync_state.json"
    if sync_state_path.exists():
        sync = _read_json(sync_state_path)
        if sync:
            if sync.get("version") != OPS_EXTRACT_SYNC_STATE_VERSION:
                sync["version"] = OPS_EXTRACT_SYNC_STATE_VERSION
                changed = True
            if sync.get("schema_version") != OPS_EXTRACT_SCHEMA_VERSION:
                sync["schema_version"] = OPS_EXTRACT_SCHEMA_VERSION
                changed = True
            for item in sync.get("uploaded_files", []):
                if "verified" not in item:
                    item["verified"] = False
                    changed = True
                if "attempts" not in item:
                    item["attempts"] = 1
                    changed = True
                if "session_uri" not in item:
                    item["session_uri"] = ""
                    changed = True
            _write_json(sync_state_path, sync, dry_run=dry_run)

    stage_cache_path = run_dir / "stage_cache.json"
    if not stage_cache_path.exists():
        changed = True
        _write_json(
            stage_cache_path,
            {
                "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                "version": STAGE_CACHE_VERSION,
                "stages": {},
            },
            dry_run=dry_run,
        )

    trace_path = run_dir / "trace.jsonl"
    if not trace_path.exists():
        changed = True
        if not dry_run:
            trace_path.write_text("", encoding="utf-8")

    diagnosis_path = run_dir / "ingestion" / "pdf_diagnosis.json"
    if not diagnosis_path.exists():
        changed = True
        _write_json(
            diagnosis_path,
            {
                "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                "files": [],
                "summary": {
                    "text-embedded": 0,
                    "image-only": 0,
                    "hybrid": 0,
                    "encrypted": 0,
                    "corrupted": 0,
                },
            },
            dry_run=dry_run,
        )

    return changed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-base", default="logs/runs", help="Runs base directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    runs_base = Path(args.runs_base)
    if not runs_base.exists():
        print(f"runs_base_not_found:{runs_base}")
        return 1

    migrated = 0
    for run_dir in sorted([p for p in runs_base.iterdir() if p.is_dir()]):
        if migrate_run(run_dir, dry_run=bool(args.dry_run)):
            migrated += 1
            print(f"migrated:{run_dir}")
    print(f"total_migrated:{migrated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
