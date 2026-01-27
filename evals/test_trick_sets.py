"""Tests for Phase 2 trick sets."""

import json
from pathlib import Path

from jarvis_core.contradiction.detector import ContradictionDetector
from jarvis_core.style.language_lint import LanguageLinter

TRICK_SETS_DIR = Path("evals/trick_sets")


def test_no_evidence():
    no_evidence_path = TRICK_SETS_DIR / "no_evidence.jsonl"
    assert no_evidence_path.exists()

    cases = []
    with open(no_evidence_path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                cases.append(json.loads(line))

    assert len(cases) >= 10
    for case in cases:
        assert case["expected_gate_passed"] is False
        assert case["expected_violation"] == "MISSING_EVIDENCE_ID"
        assert "goal" in case


def test_overclaim():
    overclaim_path = TRICK_SETS_DIR / "overclaim.jsonl"
    assert overclaim_path.exists()

    cases = []
    with open(overclaim_path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                cases.append(json.loads(line))

    assert len(cases) >= 10
    linter = LanguageLinter()
    detected = 0
    for case in cases:
        text = f"This study {case['claim_strength']} {case['goal']}."
        violations = linter.check(text)
        if violations:
            detected += 1

    detection_rate = detected / len(cases)
    assert detection_rate >= 0.9


def test_contradiction():
    contradiction_path = TRICK_SETS_DIR / "contradiction.jsonl"
    assert contradiction_path.exists()

    cases = []
    with open(contradiction_path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                cases.append(json.loads(line))

    assert len(cases) >= 10
    detector = ContradictionDetector()
    detected = 0
    for case in cases:
        claims = [item["text"] for item in case["claims"]]
        contradictions = detector.detect(claims)
        if contradictions:
            detected += 1

    detection_rate = detected / len(cases)
    assert detection_rate >= 0.85
