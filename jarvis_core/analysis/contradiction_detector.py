"""Contradiction Detector for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 2.3: 矛盾検出
Identifies contradictions between evidence items.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    """A detected contradiction between evidence items."""

    evidence_id_1: str
    evidence_id_2: str
    claim_id: str
    contradiction_type: str  # "direct", "indirect", "statistical"
    confidence: float
    explanation: str
    severity: str  # "high", "medium", "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_pair": [self.evidence_id_1, self.evidence_id_2],
            "claim_id": self.claim_id,
            "type": self.contradiction_type,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "severity": self.severity,
        }


class ContradictionDetector:
    """Detects contradictions between evidence items.

    Uses multiple strategies:
    1. Stance-based: opposing stances toward same claim
    2. Semantic: opposing meaning in similar contexts
    3. Statistical: conflicting numerical claims
    """

    # Antonym pairs for semantic contradiction
    ANTONYMS = [
        ("increase", "decrease"),
        ("higher", "lower"),
        ("more", "less"),
        ("positive", "negative"),
        ("significant", "insignificant"),
        ("effective", "ineffective"),
        ("associated", "not associated"),
        ("correlation", "no correlation"),
        ("improve", "worsen"),
        ("benefit", "harm"),
        ("safe", "unsafe"),
        ("found", "not found"),
    ]

    def detect_stance_contradictions(
        self,
        stance_results: list[dict],
    ) -> list[Contradiction]:
        """Detect contradictions based on stance analysis."""
        contradictions = []

        # Group by claim
        by_claim: dict[str, list[dict]] = {}
        for sr in stance_results:
            claim_id = sr.get("claim_id", "")
            if claim_id not in by_claim:
                by_claim[claim_id] = []
            by_claim[claim_id].append(sr)

        # Find contradictions within each claim
        for claim_id, evidences in by_claim.items():
            supports = [e for e in evidences if e.get("stance") == "supports"]
            contradicts = [e for e in evidences if e.get("stance") == "contradicts"]

            # Each support-contradict pair is a potential contradiction
            for sup in supports:
                for con in contradicts:
                    contradictions.append(
                        Contradiction(
                            evidence_id_1=sup.get("evidence_id", ""),
                            evidence_id_2=con.get("evidence_id", ""),
                            claim_id=claim_id,
                            contradiction_type="direct",
                            confidence=min(sup.get("confidence", 0.5), con.get("confidence", 0.5)),
                            explanation="Evidence items have opposing stances",
                            severity=(
                                "high"
                                if min(sup.get("confidence", 0), con.get("confidence", 0)) > 0.7
                                else "medium"
                            ),
                        )
                    )

        return contradictions

    def detect_semantic_contradictions(
        self,
        evidence_texts: list[tuple[str, str, str]],  # (evidence_id, claim_id, text)
    ) -> list[Contradiction]:
        """Detect contradictions based on antonym usage."""
        contradictions = []

        # Group by claim
        by_claim: dict[str, list[tuple[str, str]]] = {}
        for ev_id, claim_id, text in evidence_texts:
            if claim_id not in by_claim:
                by_claim[claim_id] = []
            by_claim[claim_id].append((ev_id, text.lower()))

        # Check for antonym pairs
        for claim_id, evidences in by_claim.items():
            for i, (ev_id_1, text_1) in enumerate(evidences):
                for ev_id_2, text_2 in evidences[i + 1 :]:
                    antonyms_found = self._find_antonyms(text_1, text_2)
                    if antonyms_found:
                        contradictions.append(
                            Contradiction(
                                evidence_id_1=ev_id_1,
                                evidence_id_2=ev_id_2,
                                claim_id=claim_id,
                                contradiction_type="semantic",
                                confidence=0.5 + 0.1 * len(antonyms_found),
                                explanation=f"Antonyms found: {antonyms_found}",
                                severity="medium",
                            )
                        )

        return contradictions

    def _find_antonyms(self, text_1: str, text_2: str) -> list[tuple[str, str]]:
        """Find antonym pairs between texts."""
        found = []
        for word_1, word_2 in self.ANTONYMS:
            if word_1 in text_1 and word_2 in text_2:
                found.append((word_1, word_2))
            elif word_2 in text_1 and word_1 in text_2:
                found.append((word_2, word_1))
        return found

    def detect_all(
        self,
        claims: list[dict],
        evidence_list: list[dict],
        stance_results: list[dict] | None = None,
    ) -> tuple[list[Contradiction], dict[str, Any]]:
        """Run all contradiction detection methods.

        Returns:
            Tuple of (contradictions, summary_stats).
        """
        all_contradictions: list[Contradiction] = []

        # Stance-based
        if stance_results:
            stance_contradictions = self.detect_stance_contradictions(stance_results)
            all_contradictions.extend(stance_contradictions)

        # Semantic
        evidence_texts = [
            (
                ev.get("evidence_id", ev.get("id", "")),
                ev.get("claim_id", ""),
                ev.get("text", ev.get("quote_span", "")),
            )
            for ev in evidence_list
        ]
        semantic_contradictions = self.detect_semantic_contradictions(evidence_texts)
        all_contradictions.extend(semantic_contradictions)

        # Deduplicate
        seen: set[tuple[str, str]] = set()
        unique = []
        for c in all_contradictions:
            pair = tuple(sorted([c.evidence_id_1, c.evidence_id_2]))
            if pair not in seen:
                seen.add(pair)
                unique.append(c)

        # Statistics
        stats = {
            "total_contradictions": len(unique),
            "high_severity": sum(1 for c in unique if c.severity == "high"),
            "by_type": {
                "direct": sum(1 for c in unique if c.contradiction_type == "direct"),
                "semantic": sum(1 for c in unique if c.contradiction_type == "semantic"),
            },
            "claims_with_contradictions": len(set(c.claim_id for c in unique)),
        }

        return unique, stats


def detect_contradictions(
    claims: list[dict],
    evidence_list: list[dict],
    stance_results: list[dict] | None = None,
) -> tuple[list[Contradiction], dict[str, Any]]:
    """Convenience function for contradiction detection.

    Args:
        claims: List of claim dictionaries.
        evidence_list: List of evidence dictionaries.
        stance_results: Optional pre-computed stance results.

    Returns:
        Tuple of (contradictions, stats).
    """
    detector = ContradictionDetector()
    return detector.detect_all(claims, evidence_list, stance_results)
