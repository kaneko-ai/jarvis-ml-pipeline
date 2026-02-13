"""Project Contract Check.

Per RP-177, ensures project meets evaluation requirements.
"""

from __future__ import annotations

import sys
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class ContractCheck:
    """Result of a contract check."""

    name: str
    passed: bool
    message: str


def check_eval_schema() -> ContractCheck:
    """Check that condensed evaluation spec exists in docs hub."""
    path = Path("docs/README.md")
    exists = path.exists()
    has_spec = False
    if exists:
        content = path.read_text(encoding="utf-8")
        has_spec = "Evaluation Metrics Spec" in content

    return ContractCheck(
        name="Eval Schema",
        passed=exists and has_spec,
        message=(
            "Evaluation Metrics Spec section found"
            if exists and has_spec
            else "Missing Evaluation Metrics Spec section in docs/README.md"
        ),
    )


def check_telemetry_contract() -> ContractCheck:
    """Check that telemetry contract tests exist."""
    path = Path("tests/test_telemetry_contract_v2.py")
    exists = path.exists()

    return ContractCheck(
        name="Telemetry Contract",
        passed=exists,
        message="Contract tests found" if exists else "Missing test_telemetry_contract_v2.py",
    )


def check_core_tests() -> ContractCheck:
    """Check that core tests exist and are marked."""
    path = Path("pytest.ini")
    if not path.exists():
        return ContractCheck(
            name="Core Tests",
            passed=False,
            message="Missing pytest.ini",
        )

    content = path.read_text()
    has_core_marker = "core" in content

    return ContractCheck(
        name="Core Tests",
        passed=has_core_marker,
        message="Core marker defined" if has_core_marker else "Core marker not in pytest.ini",
    )


def check_state_baseline() -> ContractCheck:
    """Check condensed state baseline exists in docs hub."""
    path = Path("docs/README.md")
    exists = path.exists()
    has_baseline = False
    if exists:
        content = path.read_text(encoding="utf-8")
        has_baseline = re.search(r"core_test_collected:\s*\d+", content) is not None

    return ContractCheck(
        name="State Baseline",
        passed=exists and has_baseline,
        message=(
            "State Baseline values found"
            if exists and has_baseline
            else "Missing core_test_collected baseline in docs/README.md"
        ),
    )


def run_all_checks() -> List[ContractCheck]:
    """Run all contract checks."""
    return [
        check_eval_schema(),
        check_telemetry_contract(),
        check_core_tests(),
        check_state_baseline(),
    ]


def format_report(checks: List[ContractCheck]) -> str:
    """Format check results."""
    lines = ["Project Contract Check", "=" * 40, ""]

    for check in checks:
        status = "[PASS]" if check.passed else "[FAIL]"
        lines.append(f"{status} {check.name}: {check.message}")

    passed = sum(1 for c in checks if c.passed)
    total = len(checks)
    lines.append("")
    lines.append(f"Result: {passed}/{total} passed")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    checks = run_all_checks()
    print(format_report(checks))

    if all(c.passed for c in checks):
        print("\n[PASS] Project meets contract requirements")
        sys.exit(0)
    else:
        print("\n[FAIL] Project contract violations found")
        sys.exit(1)


if __name__ == "__main__":
    main()
