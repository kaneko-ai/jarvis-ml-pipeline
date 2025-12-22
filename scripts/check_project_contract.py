"""Project Contract Check.

Per RP-177, ensures project meets evaluation requirements.
"""
from __future__ import annotations

import sys
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
    """Check that eval schema exists."""
    path = Path("docs/evals/metrics_spec.md")
    exists = path.exists()

    return ContractCheck(
        name="Eval Schema",
        passed=exists,
        message="metrics_spec.md found" if exists else "Missing docs/evals/metrics_spec.md",
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
    """Check state baseline exists."""
    path = Path("docs/STATE_BASELINE.md")
    exists = path.exists()

    return ContractCheck(
        name="State Baseline",
        passed=exists,
        message="STATE_BASELINE.md found" if exists else "Missing docs/STATE_BASELINE.md",
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
        status = "✓" if check.passed else "✗"
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
        print("\n✓ Project meets contract requirements")
        sys.exit(0)
    else:
        print("\n✗ Project contract violations found")
        sys.exit(1)


if __name__ == "__main__":
    main()
