"""Assign heuristic quality tags to claims."""
from __future__ import annotations

from collections.abc import Mapping


def assign_quality_tags(claim: Mapping) -> dict:
    evidence = claim.get("evidence") or []
    evidence_count = len(evidence)
    max_score = 0.0
    for item in evidence:
        try:
            max_score = max(max_score, float(item.get("score", 0.0)))
        except (TypeError, ValueError):
            continue

    if evidence_count >= 2 or max_score >= 0.7:
        strength = "high"
    elif evidence_count == 1 or max_score >= 0.4:
        strength = "med"
    else:
        strength = "low"

    tier = "C"
    if strength == "high":
        tier = "A"
    elif strength == "med":
        tier = "B"

    needs_followup = strength == "low"

    return {
        "evidence_strength": strength,
        "tier": tier,
        "conflict": False,
        "needs_followup": needs_followup,
        "note": "（推測です）" if needs_followup else "",
    }
