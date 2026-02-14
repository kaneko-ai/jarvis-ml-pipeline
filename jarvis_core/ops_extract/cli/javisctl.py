"""Unified CLI for ops_extract operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jarvis_core.app import run_task
from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.doctor import run_doctor
from jarvis_core.ops_extract.drive_repair import repair_duplicate_folders
from jarvis_core.ops_extract.drive_sync import sync_run_to_drive
from jarvis_core.ops_extract.runbook import generate_runbook
from jarvis_core.ops_extract.scoreboard import generate_weekly_report
from jarvis_core.ops_extract.sync_queue import load_sync_queue, mark_sync_queue_state


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _cmd_run(args: argparse.Namespace) -> int:
    task_dict = {
        "goal": f"OpsExtract for project {args.project}",
        "mode": "ops_extract",
        "project": args.project,
        "inputs": {"pdf_paths": args.inputs},
    }
    if args.run_id:
        task_dict["run_id"] = args.run_id
    run_config = {
        "extra": {
            "ops_extract": {
                "enabled": True,
                "sync": {
                    "enabled": bool(args.sync_enabled),
                    "dry_run": bool(args.sync_dry_run),
                },
            }
        }
    }
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


def _cmd_status(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    meta = _read_json(run_dir / "run_metadata.json")
    sync_state = _read_json(run_dir / "sync_state.json")
    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "status": meta.get("status", "unknown"),
                "finished_at": meta.get("finished_at", ""),
                "sync_state": sync_state.get("state", "not_started"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _cmd_tail(args: argparse.Namespace) -> int:
    trace = Path(args.run_dir) / "trace.jsonl"
    if not trace.exists():
        print("trace_not_found")
        return 1
    lines = trace.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in lines[-max(1, int(args.lines)) :]:
        print(line)
    return 0


def _cmd_cancel(args: argparse.Namespace) -> int:
    marker = Path(args.run_dir) / ".cancel_requested"
    marker.write_text("cancel_requested\n", encoding="utf-8")
    print(str(marker))
    return 0


def _cmd_sync(args: argparse.Namespace) -> int:
    queue_dir = Path(args.queue_dir)
    items = load_sync_queue(queue_dir)
    if args.only_human_action:
        items = [
            item
            for item in items
            if str(item.get("state", "")) in {"failed", "human_action_required"}
        ]
    for item in items:
        path = Path(str(item.get("_path", "")))
        run_dir = Path(str(item.get("run_dir", "")))
        if not run_dir.exists():
            mark_sync_queue_state(path, state="human_action_required", error="run_dir_not_found")
            continue
        mark_sync_queue_state(path, state="in_progress")
        state = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=bool(args.dry_run),
            upload_workers=max(1, int(args.upload_workers)),
            access_token=args.access_token,
            folder_id=str(item.get("drive_folder_id", "") or None),
            api_base_url=args.api_base_url,
            upload_base_url=args.upload_base_url,
            verify_sha256=not bool(args.no_verify),
        )
        if str(state.get("state", "")) == "committed":
            mark_sync_queue_state(path, state="done", error="")
        elif str(state.get("state", "")) == "deferred":
            mark_sync_queue_state(path, state="deferred", error=str(state.get("last_error", "")))
        else:
            mark_sync_queue_state(path, state="failed", error=str(state.get("last_error", "")))
    print(json.dumps({"processed": len(items)}, ensure_ascii=False))
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    sync_state = _read_json(run_dir / "sync_state.json")
    outputs = manifest.get("outputs", []) if isinstance(manifest, dict) else []
    uploaded = {
        str(item.get("path", "")).strip()
        for item in (sync_state.get("uploaded_files", []) if isinstance(sync_state, dict) else [])
        if str(item.get("path", "")).strip()
    }
    missing = []
    for output in outputs:
        path = str((output or {}).get("path", "")).strip()
        if path and path not in uploaded and path != "manifest.json":
            missing.append(path)
    print(json.dumps({"missing_remote": missing}, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


def _cmd_doctor(args: argparse.Namespace) -> int:
    report = run_doctor(
        config=OpsExtractConfig(
            enabled=True,
            sync_queue_dir=args.queue_dir,
            drive_api_base_url=args.api_base_url,
        ),
        queue_dir=Path(args.queue_dir),
    )
    print(str(report))
    return 0


def _cmd_weekly_report(_args: argparse.Namespace) -> int:
    score = generate_weekly_report()
    print(
        json.dumps(
            {
                "ops_score": score.ops_score,
                "extract_score": score.extract_score,
                "run_count": score.run_count,
                "anomalies": score.anomalies,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _cmd_repair_folders(args: argparse.Namespace) -> int:
    payload = _read_json(Path(args.folders_json))
    folders = payload.get("folders", []) if isinstance(payload, dict) else []
    report = repair_duplicate_folders(folders=folders if isinstance(folders, list) else [])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _cmd_runbook(_args: argparse.Namespace) -> int:
    path = generate_runbook()
    print(str(path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ops+Extract control CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run")
    p_run.add_argument("--project", required=True)
    p_run.add_argument("--inputs", nargs="+", required=True)
    p_run.add_argument("--run-id")
    p_run.add_argument("--sync-enabled", action="store_true")
    p_run.add_argument("--sync-dry-run", action="store_true")
    p_run.set_defaults(func=_cmd_run)

    p_status = sub.add_parser("status")
    p_status.add_argument("--run-dir", required=True)
    p_status.set_defaults(func=_cmd_status)

    p_tail = sub.add_parser("tail")
    p_tail.add_argument("--run-dir", required=True)
    p_tail.add_argument("--lines", type=int, default=30)
    p_tail.set_defaults(func=_cmd_tail)

    p_cancel = sub.add_parser("cancel")
    p_cancel.add_argument("--run-dir", required=True)
    p_cancel.set_defaults(func=_cmd_cancel)

    p_sync = sub.add_parser("sync")
    p_sync.add_argument("--queue-dir", default="sync_queue")
    p_sync.add_argument("--upload-workers", type=int, default=4)
    p_sync.add_argument("--access-token")
    p_sync.add_argument("--api-base-url")
    p_sync.add_argument("--upload-base-url")
    p_sync.add_argument("--dry-run", action="store_true")
    p_sync.add_argument("--no-verify", action="store_true")
    p_sync.add_argument("--only-human-action", action="store_true")
    p_sync.set_defaults(func=_cmd_sync)

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--run-dir", required=True)
    p_audit.set_defaults(func=_cmd_audit)

    p_doctor = sub.add_parser("doctor")
    p_doctor.add_argument("--queue-dir", default="sync_queue")
    p_doctor.add_argument("--api-base-url")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_weekly = sub.add_parser("weekly-report")
    p_weekly.set_defaults(func=_cmd_weekly_report)

    p_repair = sub.add_parser("repair-folders")
    p_repair.add_argument("--folders-json", required=True)
    p_repair.set_defaults(func=_cmd_repair_folders)

    p_runbook = sub.add_parser("runbook")
    p_runbook.set_defaults(func=_cmd_runbook)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
