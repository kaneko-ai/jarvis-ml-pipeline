"""Prune ops_extract runs based on retention policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jarvis_core.ops_extract.retention import apply_ops_extract_retention


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune ops_extract runs")
    parser.add_argument("--runs-base", default="logs/runs")
    parser.add_argument("--failed-days", type=int, default=30)
    parser.add_argument("--success-days", type=int, default=180)
    parser.add_argument("--trash-days", type=int, default=7)
    parser.add_argument("--max-delete-per-run", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--lessons", default="knowledge/failures/lessons_learned.md")
    args = parser.parse_args()

    result = apply_ops_extract_retention(
        runs_base=Path(args.runs_base),
        lessons_path=Path(args.lessons),
        failed_days=args.failed_days,
        success_days=args.success_days,
        trash_days=args.trash_days,
        max_delete_per_run=args.max_delete_per_run,
        dry_run=args.dry_run,
    )
    print(
        json.dumps(
            {
                "moved_to_trash": result.moved_to_trash,
                "deleted_from_trash": result.deleted_from_trash,
                "kept": result.kept,
                "dry_run": result.dry_run,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
