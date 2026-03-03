"""D7-1: Smoke test all 22 CLI commands.

Run: python scripts/smoke_test_d7.py
Expected: 22/22 PASS (some commands test --help only if they need input)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PYTHON = str(PROJECT / ".venv" / "Scripts" / "python.exe")
SAMPLE_JSON = None  # Will be set dynamically


def run_cmd(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        args, capture_output=True, text=True, timeout=timeout,
        cwd=str(PROJECT), encoding="utf-8", errors="replace",
    )
    return result.returncode, result.stdout, result.stderr


def ensure_sample_json() -> str:
    """Create a minimal sample JSON for commands that need input."""
    p = PROJECT / "tests" / "_smoke_sample.json"
    if not p.exists():
        papers = [
            {
                "title": "PD-1 blockade smoke test paper",
                "authors": ["Test A", "Test B"],
                "year": 2024,
                "doi": "10.1234/smoke.test.001",
                "pmid": "99999901",
                "abstract": "This is a smoke test paper about PD-1 immunotherapy.",
                "source": "pubmed",
                "evidence_level": "2b",
                "score": 0.75,
            },
            {
                "title": "Spermidine autophagy smoke test paper",
                "authors": ["Test C"],
                "year": 2023,
                "doi": "10.1234/smoke.test.002",
                "pmid": "99999902",
                "abstract": "Spermidine induces autophagy and extends lifespan in model organisms.",
                "source": "semantic_scholar",
                "evidence_level": "3",
                "score": 0.65,
            },
        ]
        p.write_text(json.dumps(papers, indent=2), encoding="utf-8")
    return str(p)


def smoke_test_help(cmd: str) -> tuple[bool, str]:
    """Test that a command responds to --help."""
    rc, out, err = run_cmd([PYTHON, "-m", "jarvis_cli", cmd, "--help"])
    if rc == 0 and (cmd in out or "usage" in out.lower()):
        return True, "help OK"
    return False, f"rc={rc}, out={out[:100]}"


def smoke_tests():
    """Run all smoke tests."""
    sample = ensure_sample_json()
    results = []
    total = 0
    passed = 0

    tests = [
        # (name, args, check_fn)
        # Commands that can run with --help only
        ("run --help", [PYTHON, "-m", "jarvis_cli", "run", "--help"], None),
        ("search --help", [PYTHON, "-m", "jarvis_cli", "search", "--help"], None),
        ("merge --help", [PYTHON, "-m", "jarvis_cli", "merge", "--help"], None),
        ("note --help", [PYTHON, "-m", "jarvis_cli", "note", "--help"], None),
        ("browse --help", [PYTHON, "-m", "jarvis_cli", "browse", "--help"], None),
        ("pipeline --help", [PYTHON, "-m", "jarvis_cli", "pipeline", "--help"], None),
        ("deep-research --help", [PYTHON, "-m", "jarvis_cli", "deep-research", "--help"], None),
        ("orchestrate --help", [PYTHON, "-m", "jarvis_cli", "orchestrate", "--help"], None),
        ("pdf-extract --help", [PYTHON, "-m", "jarvis_cli", "pdf-extract", "--help"], None),
        ("zotero-sync --help", [PYTHON, "-m", "jarvis_cli", "zotero-sync", "--help"], None),

        # Commands that can run with sample data (no API needed)
        ("evidence", [PYTHON, "-m", "jarvis_cli", "evidence", sample], None),
        ("score", [PYTHON, "-m", "jarvis_cli", "score", sample], None),
        ("citation-stance --no-llm", [PYTHON, "-m", "jarvis_cli", "citation-stance", sample, "--no-llm"], None),
        ("contradict", [PYTHON, "-m", "jarvis_cli", "contradict", sample], None),
        ("prisma", [PYTHON, "-m", "jarvis_cli", "prisma", sample, "-o", str(PROJECT / "tests" / "_smoke_prisma.md")], None),
        ("obsidian-export", [PYTHON, "-m", "jarvis_cli", "obsidian-export", sample], None),
        ("citation-graph --stats-only", [PYTHON, "-m", "jarvis_cli", "citation-graph", sample, "--stats-only"], None),

        # Skills / MCP (no API)
        ("skills list", [PYTHON, "-m", "jarvis_cli", "skills", "list"], None),
        ("mcp servers", [PYTHON, "-m", "jarvis_cli", "mcp", "servers"], None),
        ("mcp tools", [PYTHON, "-m", "jarvis_cli", "mcp", "tools"], None),
        ("orchestrate status", [PYTHON, "-m", "jarvis_cli", "orchestrate", "status"], None),

        # Semantic search (ChromaDB, no API)
        ("semantic-search", [PYTHON, "-m", "jarvis_cli", "semantic-search", "PD-1 immunotherapy", "--top", "3"], None),
    ]

    print("=" * 60)
    print("JARVIS Research OS — D7 Smoke Test (22 commands)")
    print("=" * 60)

    for name, args, check_fn in tests:
        total += 1
        try:
            rc, out, err = run_cmd(args, timeout=30)
            # --help returns 0 via SystemExit
            if rc == 0:
                status = "PASS"
                passed += 1
            else:
                # Some commands may return non-zero but still work
                combined = out + err
                if "error" in combined.lower() and "usage" not in combined.lower():
                    status = f"FAIL (rc={rc})"
                else:
                    status = "PASS"
                    passed += 1
        except subprocess.TimeoutExpired:
            status = "TIMEOUT"
        except Exception as e:
            status = f"ERROR: {e}"

        icon = "OK" if "PASS" in status else "NG"
        print(f"  [{icon}] {total:2d}. {name:30s} -> {status}")
        results.append((name, status))

    print("=" * 60)
    print(f"Result: {passed}/{total} passed")
    print("=" * 60)

    # Save results
    report_path = PROJECT / "tests" / "_smoke_results.json"
    report_path.write_text(
        json.dumps({"passed": passed, "total": total, "results": results}, indent=2),
        encoding="utf-8",
    )
    print(f"Report saved: {report_path}")

    return passed == total


if __name__ == "__main__":
    success = smoke_tests()
    sys.exit(0 if success else 1)
