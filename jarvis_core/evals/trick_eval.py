"""Trick Set Evaluation (Phase 2-ΩΩ).

Evaluates JARVIS output against trick sets (no_evidence, overclaim, contradiction)
to ensure it fails appropriately when it should.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def eval_no_evidence_set(run_dir: Path) -> dict[str, Any]:
    """Evaluate no_evidence trick set.

    Expected behavior:
    - UNSUPPORTED_CLAIM warnings should exist
    - Conclusions should not be assertive
    - gate_passed should be false

    Args:
        run_dir: Path to run directory

    Returns:
        Dict with 'passed', 'errors'
    """
    errors = []

    # Check warnings
    warnings_file = run_dir / "warnings.jsonl"
    if not warnings_file.exists():
        errors.append("warnings.jsonl not found")
        return {"passed": False, "errors": errors}

    with open(warnings_file, encoding="utf-8") as f:
        warnings = [json.loads(line) for line in f if line.strip()]

    # Should have UNSUPPORTED_CLAIM
    unsupported = [w for w in warnings if w.get("code") == "UNSUPPORTED_CLAIM"]
    if not unsupported:
        errors.append("No UNSUPPORTED_CLAIM warning found")

    # Check eval_summary
    eval_file = run_dir / "eval_summary.json"
    if eval_file.exists():
        with open(eval_file, encoding="utf-8") as f:
            eval_summary = json.load(f)

        # For no_evidence, we expect gate to fail
        if eval_summary.get("gate_passed", True):
            errors.append("gate_passed should be false for no_evidence set")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors}


def eval_overclaim_set(run_dir: Path) -> dict[str, Any]:
    """Evaluate overclaim trick set.

    Expected behavior:
    - Conclusions should use hedging language
    - No causal assertions (causes, leads to)
    - Uncertainty labels should be conservative

    Args:
        run_dir: Path to run directory

    Returns:
        Dict with 'passed', 'errors'
    """
    errors = []

    # Check report
    report_file = run_dir / "report.md"
    if not report_file.exists():
        errors.append("report.md not found")
        return {"passed": False, "errors": errors}

    with open(report_file, encoding="utf-8") as f:
        report_text = f.read()

    # Should not have causal assertions
    forbidden_terms = ["causes", "leads to", "proves", "guarantees"]
    for term in forbidden_terms:
        if term in report_text.lower():
            errors.append(f"Forbidden causal term found: '{term}'")

    # Should have hedging
    hedging_terms = ["可能性", "示唆", "考えられる", "限定的"]
    has_hedging = any(term in report_text for term in hedging_terms)
    if not has_hedging:
        errors.append("No hedging language found")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors}


def eval_contradiction_set(run_dir: Path) -> dict[str, Any]:
    """Evaluate contradiction trick set.

    Expected behavior:
    - Contradictions should be detected
    - Uncertainty should be downgraded
    - Both sides should be presented

    Args:
        run_dir: Path to run directory

    Returns:
        Dict with 'passed', 'errors'
    """
    errors = []

    # Check warnings for contradictions
    warnings_file = run_dir / "warnings.jsonl"
    if warnings_file.exists():
        with open(warnings_file, encoding="utf-8") as f:
            warnings = [json.loads(line) for line in f if line.strip()]

        # Should have contradiction warning
        contradictions = [w for w in warnings if "矛盾" in w.get("message", "")]
        if not contradictions:
            errors.append("No contradiction warning found")

    # Check report for both sides
    report_file = run_dir / "report.md"
    if report_file.exists():
        with open(report_file, encoding="utf-8") as f:
            report_text = f.read()

        # Should mention contradiction
        if "矛盾" not in report_text:
            errors.append("Report does not mention contradiction")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors}


def evaluate_trick_set(set_path: Path, run_dir: Path) -> dict[str, Any]:
    """Evaluate a trick set.

    Args:
        set_path: Path to trick set file
        run_dir: Path to run directory

    Returns:
        Dict with evaluation results
    """
    set_name = set_path.stem

    if "no_evidence" in set_name:
        return eval_no_evidence_set(run_dir)
    elif "overclaim" in set_name:
        return eval_overclaim_set(run_dir)
    elif "contradiction" in set_name:
        return eval_contradiction_set(run_dir)
    else:
        return {"passed": False, "errors": [f"Unknown trick set: {set_name}"]}


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Evaluate trick sets")
    parser.add_argument("--set", required=True, help="Path to trick set file")
    parser.add_argument("--run-dir", help="Path to run directory (default: latest)")

    args = parser.parse_args()

    set_path = Path(args.set)

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        # Find latest run
        runs_dir = Path("logs/runs")
        if runs_dir.exists():
            runs = sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            if runs:
                run_dir = runs[0]
            else:
                print("No runs found")
                sys.exit(1)
        else:
            print("logs/runs directory not found")
            sys.exit(1)

    result = evaluate_trick_set(set_path, run_dir)

    print(f"Trick Set: {set_path.name}")
    print(f"Passed: {result['passed']}")

    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("All checks passed!")
        sys.exit(0)
