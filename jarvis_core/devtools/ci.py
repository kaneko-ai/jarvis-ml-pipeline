"""CI DevTools.

Per PR-61: Single entry point for local and CI test execution.
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def run_core_tests(verbose: bool = True) -> int:
    """Run core tests only."""
    cmd = [sys.executable, "-m", "pytest", "-m", "core"]
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    result = subprocess.run(cmd)
    return result.returncode


def run_legacy_tests(verbose: bool = True) -> int:
    """Run legacy tests (non-blocking)."""
    cmd = [sys.executable, "-m", "pytest", "-m", "legacy"]
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    result = subprocess.run(cmd)
    return result.returncode


def run_all_tests(verbose: bool = True) -> int:
    """Run all tests."""
    cmd = [sys.executable, "-m", "pytest"]
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    result = subprocess.run(cmd)
    return result.returncode


def check_imports() -> int:
    """Check critical imports."""
    checks = [
        "from jarvis_core import run_jarvis",
        "from jarvis_core.app import run_task",
        "from jarvis_core.telemetry import init_logger",
    ]

    for check in checks:
        result = subprocess.run(
            [sys.executable, "-c", f"{check}; print('OK')"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"❌ Import failed: {check}")
            print(result.stderr)
            return 1
        print(f"✓ {check}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="JARVIS CI DevTools")
    subparsers = parser.add_subparsers(dest="command")

    # core-tests
    core_parser = subparsers.add_parser("core-tests", help="Run core tests")
    core_parser.add_argument("-q", "--quiet", action="store_true")

    # legacy-tests
    legacy_parser = subparsers.add_parser("legacy-tests", help="Run legacy tests")
    legacy_parser.add_argument("-q", "--quiet", action="store_true")

    # all-tests
    all_parser = subparsers.add_parser("all-tests", help="Run all tests")
    all_parser.add_argument("-q", "--quiet", action="store_true")

    # check-imports
    subparsers.add_parser("check-imports", help="Check critical imports")

    # full-ci (core + imports)
    subparsers.add_parser("full-ci", help="Full CI check (core tests + imports)")

    args = parser.parse_args()

    if args.command == "core-tests":
        sys.exit(run_core_tests(not args.quiet))
    elif args.command == "legacy-tests":
        sys.exit(run_legacy_tests(not args.quiet))
    elif args.command == "all-tests":
        sys.exit(run_all_tests(not args.quiet))
    elif args.command == "check-imports":
        sys.exit(check_imports())
    elif args.command == "full-ci":
        # Run both
        import_result = check_imports()
        if import_result != 0:
            sys.exit(import_result)
        sys.exit(run_core_tests(True))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
