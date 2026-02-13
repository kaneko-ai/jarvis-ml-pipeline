"""CLI entry point for ops_extract mode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jarvis_core.app import run_task


def _load_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ops_extract pipeline")
    parser.add_argument("--project", default="default", help="Project name")
    parser.add_argument("--input", nargs="+", required=True, help="Input PDF files")
    parser.add_argument("--run-id", help="Optional run_id")
    parser.add_argument("--config", help="Optional JSON config path")
    parser.add_argument("--dry-run", action="store_true", help="Enable dry-run flag")
    parser.add_argument("--sync-enabled", action="store_true", help="Enable post-run sync")
    parser.add_argument("--sync-real", action="store_true", help="Use real sync (not dry-run)")
    parser.add_argument("--sync-max-retries", type=int, help="Sync retry upper bound")
    parser.add_argument("--sync-retry-backoff-sec", type=float, help="Sync retry backoff seconds")
    parser.add_argument(
        "--sync-no-verify-sha256",
        action="store_true",
        help="Disable sync SHA256 verification",
    )
    parser.add_argument("--drive-token", help="Drive access token for real sync")
    parser.add_argument("--drive-folder", help="Drive folder id")
    parser.add_argument(
        "--lessons-path",
        help="Path to lessons_learned.md (default uses project setting/environment)",
    )
    parser.add_argument(
        "--min-disk-free-gb",
        type=float,
        help="Preflight minimum free disk space in GB",
    )
    parser.add_argument(
        "--warn-only-preflight",
        action="store_true",
        help="Do not stop run when preflight fails",
    )
    parser.add_argument(
        "--preflight-rule-mode",
        choices=["strict", "warn"],
        help="Preflight rule mode",
    )
    parser.add_argument("--retention-failed-days", type=int)
    parser.add_argument("--retention-success-days", type=int)
    parser.add_argument("--retention-trash-days", type=int)
    parser.add_argument("--retention-max-delete-per-run", type=int)
    parser.add_argument("--retention-dry-run", action="store_true")
    args = parser.parse_args()

    cfg = _load_config(args.config)
    extra = cfg.get("extra", {}) if isinstance(cfg, dict) else {}
    ops_extract = extra.get("ops_extract", {}) if isinstance(extra, dict) else {}
    ops_extract["enabled"] = True
    if args.dry_run:
        ops_extract["dry_run"] = True
    sync_cfg = ops_extract.get("sync", {})
    if args.sync_enabled:
        sync_cfg["enabled"] = True
    if args.sync_real:
        sync_cfg["dry_run"] = False
    if args.sync_max_retries is not None:
        sync_cfg["max_retries"] = args.sync_max_retries
    if args.sync_retry_backoff_sec is not None:
        sync_cfg["retry_backoff_sec"] = args.sync_retry_backoff_sec
    if args.sync_no_verify_sha256:
        sync_cfg["verify_sha256"] = False
    ops_extract["sync"] = sync_cfg
    drive_cfg = ops_extract.get("drive", {})
    if args.drive_token:
        drive_cfg["access_token"] = args.drive_token
    if args.drive_folder:
        drive_cfg["folder_id"] = args.drive_folder
    if drive_cfg:
        ops_extract["drive"] = drive_cfg
    if args.lessons_path:
        ops_extract["lessons_path"] = args.lessons_path
    if args.min_disk_free_gb is not None:
        ops_extract["min_disk_free_gb"] = args.min_disk_free_gb
    if args.warn_only_preflight:
        ops_extract["stop_on_preflight_failure"] = False
    if args.preflight_rule_mode:
        preflight_cfg = ops_extract.get("preflight", {})
        preflight_cfg["rule_mode"] = args.preflight_rule_mode
        ops_extract["preflight"] = preflight_cfg

    retention_cfg = ops_extract.get("retention", {})
    if args.retention_failed_days is not None:
        retention_cfg["failed_days"] = args.retention_failed_days
    if args.retention_success_days is not None:
        retention_cfg["success_days"] = args.retention_success_days
    if args.retention_trash_days is not None:
        retention_cfg["trash_days"] = args.retention_trash_days
    if args.retention_max_delete_per_run is not None:
        retention_cfg["max_delete_per_run"] = args.retention_max_delete_per_run
    if args.retention_dry_run:
        retention_cfg["dry_run"] = True
    if retention_cfg:
        ops_extract["retention"] = retention_cfg
    extra["ops_extract"] = ops_extract

    run_config = {
        "extra": extra,
        "seed": cfg.get("seed"),
        "model": cfg.get("model", "ops_extract-local"),
        "provider": cfg.get("provider", "mock"),
    }

    task_dict = {
        "goal": f"OpsExtract for project {args.project}",
        "mode": "ops_extract",
        "project": args.project,
        "inputs": {"pdf_paths": args.input},
    }
    if args.run_id:
        task_dict["run_id"] = args.run_id

    result = run_task(task_dict, run_config)
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "status": result.status,
                "log_dir": result.log_dir,
                "warnings": result.warnings,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
