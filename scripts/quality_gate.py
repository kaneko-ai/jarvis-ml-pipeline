#!/usr/bin/env python
"""Quality gate utilities.

This script supports two modes:
1. Legacy run-dir mode (`--run-dir`) to evaluate run artifacts.
2. CI mode (`--ci`) to run required/optional quality checks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CITATION_PATTERN = re.compile(r"\[[0-9]+\]")


@dataclass
class GateResult:
    """A single quality gate execution result."""

    name: str
    passed: bool
    message: str
    required: bool = True


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON content safely."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {}


def detect_citations_attached(report_path: Path) -> bool:
    """Detect whether report contains at least one citation-like marker."""
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
    """Count warning lines in JSONL warning file."""
    if not log_path.exists():
        return 0
    try:
        with log_path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def evaluate_quality_gate(run_dir: Path) -> dict[str, Any]:
    """Evaluate legacy run-directory based quality gate."""
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

    reasons: list[str] = []
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


def run_command(
    command: list[str],
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Run command and return returncode/output pair."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=merged_env,
        )
        output = (completed.stdout + completed.stderr).strip()
        return completed.returncode, output
    except subprocess.TimeoutExpired:
        return -1, f"Timeout after {timeout}s"
    except FileNotFoundError:
        return -1, f"Command not found: {command[0]}"


def _tail(text: str, limit: int = 260) -> str:
    """Return compact tail output for gate messages."""
    if len(text) <= limit:
        return text
    return text[-limit:]


def check_ruff() -> GateResult:
    code, output = run_command(["uv", "run", "ruff", "check", "jarvis_core", "tests"])
    return GateResult("ruff", code == 0, _tail(output))


def check_black() -> GateResult:
    code, output = run_command(["uv", "run", "black", "--check", "jarvis_core", "tests"])
    return GateResult("black", code == 0, _tail(output))


def check_pytest() -> GateResult:
    code, output = run_command(
        [
            "uv",
            "run",
            "pytest",
            "tests/",
            "-x",
            "--ignore=tests/e2e",
            "--ignore=tests/integration",
            "-p",
            "no:randomly",
            "-p",
            "no:xdist",
            "-q",
            "--tb=line",
            "--no-header",
        ],
        timeout=1800,
    )
    return GateResult("pytest", code == 0, _tail(output))


def check_coverage() -> GateResult:
    coverage_dir = Path(tempfile.gettempdir()) / "jarvis_quality_gate_coverage"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    for coverage_file in coverage_dir.glob(".coverage*"):
        try:
            coverage_file.unlink()
        except OSError:
            # Cleanup failures are non-fatal; pytest-cov will create a new DB file.
            continue

    code, output = run_command(
        [
            "uv",
            "run",
            "pytest",
            "tests/",
            "--cov=jarvis_core",
            "--cov-fail-under=70",
            "--ignore=tests/e2e",
            "--ignore=tests/integration",
            "-p",
            "no:randomly",
            "-p",
            "no:xdist",
            "-q",
            "--tb=no",
            "--no-header",
        ],
        timeout=1800,
        env={"COVERAGE_FILE": str(coverage_dir / ".coverage")},
    )
    return GateResult("coverage>=70", code == 0, _tail(output))


def check_bundle_contract() -> GateResult:
    code, output = run_command(["uv", "run", "python", "scripts/validate_bundle.py"])
    return GateResult("bundle-contract", code == 0, _tail(output))


def check_mypy() -> GateResult:
    code, output = run_command(
        [
            "uv",
            "run",
            "mypy",
            "--explicit-package-bases",
            "--follow-imports=skip",
            "--ignore-missing-imports",
            "jarvis_core/evidence/",
            "jarvis_core/contradiction/",
            "jarvis_core/citation/",
            "jarvis_core/sources/",
        ],
        timeout=1200,
    )
    return GateResult("mypy-core", code == 0, _tail(output), required=False)


def check_bandit() -> GateResult:
    code, output = run_command(["bandit", "-r", "jarvis_core", "-ll", "-q"], timeout=1200)
    return GateResult("bandit", code == 0, _tail(output), required=False)


def collect_ci_gates() -> list[GateResult]:
    """Collect all CI gate execution results."""
    return [
        check_ruff(),
        check_black(),
        check_pytest(),
        check_coverage(),
        check_bundle_contract(),
        check_mypy(),
        check_bandit(),
    ]


def evaluate_ci_gates(gates: list[GateResult]) -> dict[str, Any]:
    """Evaluate gate outcomes and aggregate pass/fail counts."""
    required_failures = sum(1 for gate in gates if gate.required and not gate.passed)
    optional_failures = sum(1 for gate in gates if not gate.required and not gate.passed)
    return {
        "required_failures": required_failures,
        "optional_failures": optional_failures,
        "all_required_passed": required_failures == 0,
        "gates": [asdict(gate) for gate in gates],
    }


def print_ci_report(summary: dict[str, Any]) -> None:
    """Print human-readable CI gate report."""
    print("=" * 60)
    print("QUALITY GATE REPORT")
    print("=" * 60)
    for gate in summary["gates"]:
        if gate["passed"]:
            icon = "PASS"
        elif gate["required"]:
            icon = "FAIL"
        else:
            icon = "WARN"
        level = "REQUIRED" if gate["required"] else "OPTIONAL"
        print(f"[{icon}] [{level}] {gate['name']}")
        if gate["message"]:
            print(f"  {gate['message']}")

    print("=" * 60)
    if summary["all_required_passed"]:
        print("ALL REQUIRED GATES PASSED")
    else:
        print(f"REQUIRED GATE FAILURES: {summary['required_failures']}")


def run_ci_quality_gate(as_json: bool) -> int:
    """Run unified CI gates and return process exit code."""
    summary = evaluate_ci_gates(collect_ci_gates())

    if as_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_ci_report(summary)

    return 0 if summary["all_required_passed"] else 1


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Quality gate utility")
    parser.add_argument("--run-dir", help="Path to run directory (legacy mode)")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    parser.add_argument("--ci", action="store_true", help="Run integrated CI quality gates")
    args = parser.parse_args()

    if args.ci:
        return run_ci_quality_gate(args.json)

    if not args.run_dir:
        parser.error("--run-dir is required unless --ci is set")

    result = evaluate_quality_gate(Path(args.run_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["gate_passed"] else "FAIL"
        print(f"Quality Gate v1: {status} - {result['gate_reason']}")

    return 0 if result["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
