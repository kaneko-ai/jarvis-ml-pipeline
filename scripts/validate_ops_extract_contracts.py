"""Validate ops_extract run artifacts against JSON Schemas."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jarvis_core.ops_extract.schema_validate import validate_run_contracts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run_dirs",
        nargs="+",
        help="Run directory path(s) containing ops_extract artifacts",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    all_errors: list[str] = []
    for run_dir_raw in args.run_dirs:
        run_dir = Path(run_dir_raw)
        if not run_dir.exists():
            all_errors.append(f"{run_dir}:not_found")
            continue
        errors = validate_run_contracts(run_dir)
        all_errors.extend([f"{run_dir}:{err}" for err in errors])

    if all_errors:
        print("OPS_EXTRACT_CONTRACTS: FAIL")
        for item in all_errors:
            print(f"- {item}")
        return 1

    print("OPS_EXTRACT_CONTRACTS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
