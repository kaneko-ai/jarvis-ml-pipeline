#!/usr/bin/env python
"""Quality Gate v1 evaluator."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CITATION_PATTERN = re.compile(r"\[[0-9]+\]")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def detect_citations_attached(report_path: Path) -> bool:
    if not report_path.exists():
        return False
    try:
        content = report_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = report_path.read_text(encoding="utf-8", errors="ignore")
    if not content.strip():
        return False
    return bool(CITATION_PATTERN.search(content) or "http" in content)


def count_warnings(log_path: Path) -> int:
    if not log_path.exists():
        return 0
    try:
        with log_path.open("r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


def evaluate_quality_gate(run_dir: Path) -> dict[str, Any]:
    summary = load_json(run_dir / "summary.json")
    stats = load_json(run_dir / "stats.json")
    warnings_path = run_dir / "warnings.jsonl"
    report_path = run_dir / "report.md"

    papers_found = stats.get("meta")
    if papers_found is None:
        papers_found = summary.get("papers", 0)
    papers_found = int(papers_found or 0)

    papers_processed = int(stats.get("chunks", 0) or 0)
    report_exists = report_path.exists()
    citations_attached = detect_citations_attached(report_path)

    reasons = []
    if papers_found < 1:
        reasons.append("No papers found")
    if not report_exists:
        reasons.append("report.md missing")
    if not citations_attached:
        reasons.append("Citations not attached")

    gate_passed = len(reasons) == 0
    gate_reason = "Gate passed" if gate_passed else "; ".join(reasons)

    return {
        "gate_passed": gate_passed,
        "gate_reason": gate_reason,
        "papers_found": papers_found,
        "papers_processed": papers_processed,
        "citations_attached": citations_attached,
        "report_exists": report_exists,
        "warnings_count": count_warnings(warnings_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Quality Gate v1")
    parser.add_argument("--run-dir", required=True, help="Path to run directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = parser.parse_args()

    result = evaluate_quality_gate(Path(args.run_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["gate_passed"] else "FAIL"
        print(f"Quality Gate v1: {status} - {result['gate_reason']}")

    return 0 if result["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
