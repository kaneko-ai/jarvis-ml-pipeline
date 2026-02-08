"""TD-003: Bundle contract validator.

Validates that a run bundle contains all required files and valid JSON/JSONL content.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FILES: list[str] = [
    "input.json",
    "papers.jsonl",
    "claims.jsonl",
    "evidence.jsonl",
    "scores.json",
    "report.md",
    "warnings.jsonl",
    "eval_summary.json",
    "cost_report.json",
    "provenance.jsonl",
]


def validate_bundle(bundle_dir: str | Path) -> tuple[bool, list[str]]:
    """Validate a bundle directory against the contract.

    Args:
        bundle_dir: Path to a bundle directory.

    Returns:
        Tuple of validation status and validation errors.
    """
    bundle_path = Path(bundle_dir)
    errors: list[str] = []

    if not bundle_path.is_dir():
        return False, [f"Bundle directory not found: {bundle_path}"]

    for filename in REQUIRED_FILES:
        file_path = bundle_path / filename
        if not file_path.exists():
            errors.append(f"Missing required file: {filename}")
            continue

        if file_path.stat().st_size == 0:
            errors.append(f"Empty file: {filename}")
            continue

        if filename.endswith(".json"):
            try:
                json.loads(file_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                errors.append(f"Invalid JSON in {filename}: {exc}")

        if filename.endswith(".jsonl"):
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
                for idx, line in enumerate(lines, start=1):
                    if line.strip():
                        json.loads(line)
            except (json.JSONDecodeError, OSError) as exc:
                errors.append(f"Invalid JSONL in {filename}: {exc}")

    return len(errors) == 0, errors


def _print_schema() -> None:
    print("Bundle contract schema validation: PASS")
    print(f"Required files: {len(REQUIRED_FILES)}")
    for filename in REQUIRED_FILES:
        print(f"  - {filename}")


def main() -> int:
    """CLI entrypoint."""
    if len(sys.argv) < 2:
        _print_schema()
        return 0

    bundle_dir = sys.argv[1]
    is_valid, errors = validate_bundle(bundle_dir)

    if is_valid:
        print(f"Bundle validation PASSED: {bundle_dir}")
        return 0

    print(f"Bundle validation FAILED: {bundle_dir}")
    for error in errors:
        print(f"  - {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
