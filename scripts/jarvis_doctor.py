"""Jarvis Doctor.

Per RP-164, provides environment diagnostics.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    passed: bool
    message: str
    fix_hint: str = ""


def check_python_version() -> DiagnosticResult:
    """Check Python version."""
    version = sys.version_info
    ok = version.major == 3 and version.minor >= 9

    return DiagnosticResult(
        name="Python Version",
        passed=ok,
        message=f"Python {version.major}.{version.minor}.{version.micro}",
        fix_hint="Python 3.9+ required" if not ok else "",
    )


def check_imports() -> DiagnosticResult:
    """Check core imports."""
    missing = []

    try:
        import jarvis_core
    except ImportError:
        missing.append("jarvis_core")

    try:
        import jarvis_tools
    except ImportError:
        missing.append("jarvis_tools")

    ok = len(missing) == 0
    return DiagnosticResult(
        name="Core Imports",
        passed=ok,
        message="OK" if ok else f"Missing: {', '.join(missing)}",
        fix_hint="Run: pip install -e ." if not ok else "",
    )


def check_data_dirs() -> DiagnosticResult:
    """Check data directories exist and are writable."""
    dirs = ["logs", "data/runs", "reports"]
    issues = []

    for d in dirs:
        path = Path(d)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"{d}: cannot create ({e})")
        else:
            # Check writable
            test_file = path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                issues.append(f"{d}: not writable")

    ok = len(issues) == 0
    return DiagnosticResult(
        name="Data Directories",
        passed=ok,
        message="OK" if ok else "; ".join(issues),
        fix_hint="Check permissions" if not ok else "",
    )


def check_network_mode() -> DiagnosticResult:
    """Check network isolation mode."""
    no_network = os.environ.get("NO_NETWORK", "0") == "1"

    return DiagnosticResult(
        name="Network Mode",
        passed=True,
        message="Isolated (NO_NETWORK=1)" if no_network else "Network enabled",
        fix_hint="",
    )


def check_pdf_engines() -> DiagnosticResult:
    """Check PDF extraction engines."""
    engines = []

    try:
        import fitz

        engines.append("pymupdf")
    except ImportError:
        pass

    try:
        from pdfminer.high_level import extract_text

        engines.append("pdfminer")
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader

        engines.append("pypdf2")
    except ImportError:
        pass

    ok = len(engines) > 0
    return DiagnosticResult(
        name="PDF Engines",
        passed=ok,
        message=f"Available: {', '.join(engines)}" if engines else "None installed",
        fix_hint="pip install PyMuPDF pdfminer.six PyPDF2" if not ok else "",
    )


def run_diagnostics() -> List[DiagnosticResult]:
    """Run all diagnostics."""
    return [
        check_python_version(),
        check_imports(),
        check_data_dirs(),
        check_network_mode(),
        check_pdf_engines(),
    ]


def format_diagnostics(results: List[DiagnosticResult]) -> str:
    """Format diagnostics as text."""
    lines = ["JARVIS Doctor", "=" * 40, ""]

    for r in results:
        status = "✓" if r.passed else "✗"
        lines.append(f"{status} {r.name}: {r.message}")
        if r.fix_hint:
            lines.append(f"  → Fix: {r.fix_hint}")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    lines.append("")
    lines.append(f"Result: {passed}/{total} checks passed")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    results = run_diagnostics()
    print(format_diagnostics(results))

    if all(r.passed for r in results):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
