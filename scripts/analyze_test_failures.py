#!/usr/bin/env python3
"""Analyze test failures and categorize them."""

import subprocess
import json
import re
from pathlib import Path
from collections import defaultdict


def run_tests_and_collect_failures():
    """Run pytest and collect failure information."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "tests/",
            "--ignore=tests/e2e",
            "--ignore=tests/integration",
            "-v",
            "--tb=short",
            "-q",
            "--no-header",
            "-x",  # Stop on first failure for initial analysis
            "--collect-only",
            "-q",
        ],
        capture_output=True,
        text=True,
    )
    return result


def categorize_failures(output: str) -> dict:
    """Categorize failures by type."""
    categories = defaultdict(list)

    patterns = {
        "import_error": r"ImportError|ModuleNotFoundError",
        "attribute_error": r"AttributeError",
        "type_error": r"TypeError",
        "value_error": r"ValueError",
        "assertion_error": r"AssertionError",
        "file_not_found": r"FileNotFoundError",
        "connection_error": r"ConnectionError|ConnectionRefusedError",
        "timeout": r"TimeoutError|Timeout",
        "fixture_error": r"fixture.*not found|FixtureLookupError",
        "mock_error": r"MagicMock|Mock.*called",
    }

    for line in output.split("\n"):
        for category, pattern in patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                categories[category].append(line)
                break

    return dict(categories)


def generate_fix_plan(categories: dict) -> dict:
    """Generate fix plan based on categories."""
    fix_plan = {
        "priority_1_quick_fixes": [],
        "priority_2_mock_fixes": [],
        "priority_3_logic_fixes": [],
        "priority_4_skip_candidates": [],
    }

    # Import errors - usually quick fixes
    if "import_error" in categories:
        fix_plan["priority_1_quick_fixes"].extend(
            [
                "Check missing dependencies in pyproject.toml",
                "Add conditional imports for optional dependencies",
                "Fix circular imports",
            ]
        )

    # Fixture errors - need conftest.py updates
    if "fixture_error" in categories:
        fix_plan["priority_2_mock_fixes"].extend(
            [
                "Add missing fixtures to tests/conftest.py",
                "Ensure fixture scope is correct",
                "Add pytest plugins if needed",
            ]
        )

    # Connection errors - need mocking
    if "connection_error" in categories:
        fix_plan["priority_2_mock_fixes"].extend(
            [
                "Mock external API calls",
                "Add @pytest.mark.network decorator",
                "Use responses or httpx_mock",
            ]
        )

    return fix_plan


def main():
    print("=== JARVIS Test Failure Analyzer ===\n")

    # Collect test list first
    print("Collecting test list...")
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "tests/",
            "--ignore=tests/e2e",
            "--ignore=tests/integration",
            "--collect-only",
        ],
        capture_output=True,
        text=True,
    )

    # Count tests - more robust way
    test_count = 0
    for line in result.stdout.split("\n"):
        if "<Function" in line or "::" in line:
            test_count += 1

    if test_count == 0:
        # Try finding "collected X items"
        match = re.search(r"collected (\d+) items", result.stdout)
        if match:
            test_count = int(match.group(1))

    print(f"Total tests found: {test_count}")

    if result.stderr:
        print("\nCollection Warnings/Errors:")
        print(result.stderr[:500])

    # Run actual tests
    print("\nRunning tests (this may take a while)...")
    # We run without -x to get more failures, but with --maxfail to avoid infinite run
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "tests/",
            "--ignore=tests/e2e",
            "--ignore=tests/integration",
            "-v",
            "--tb=line",
            "--maxfail=100",
        ],
        capture_output=True,
        text=True,
    )

    # Analyze output
    full_output = result.stdout + result.stderr
    categories = categorize_failures(full_output)

    print("\n=== Failure Categories ===")
    for category, items in categories.items():
        print(f"{category}: {len(items)} hits in output")

    # Generate fix plan
    fix_plan = generate_fix_plan(categories)

    # Save results
    output = {
        "total_tests": test_count,
        "categories": categories,
        "fix_plan": fix_plan,
        "raw_output_snippet": full_output[:2000],
    }

    output_path = Path("artifacts/test_analysis.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
