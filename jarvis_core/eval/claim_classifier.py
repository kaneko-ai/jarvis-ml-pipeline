"""Claim Classifier.

Per RP-126, classifies claims as fact or interpretation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ClaimLabel(Enum):
    """Claim classification labels."""

    FACT = "fact"
    INTERPRETATION = "interpretation"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"


# Patterns indicating interpretation/hypothesis
INTERPRETATION_PATTERNS = [
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bsuggests?\b",
    r"\bimplies?\b",
    r"\bpossibly\b",
    r"\bprobably\b",
    r"\blikely\b",
    r"\bappears?\b",
    r"\bseems?\b",
    r"\bbelieve[sd]?\b",
    r"\bthink[s]?\b",
    r"\bhypothesi[sz]e[sd]?\b",
    r"\bspeculate[sd]?\b",
    r"\bpropose[sd]?\b",
    r"\bit is (?:possible|plausible|conceivable)\b",
    r"\bwe (?:propose|suggest|hypothesize)\b",
]

# Patterns indicating factual claims
FACT_PATTERNS = [
    r"\bdemonstrated?\b",
    r"\bshowed?\b",
    r"\bconfirmed?\b",
    r"\bestablished?\b",
    r"\bdetermined?\b",
    r"\bidentified?\b",
    r"\bobserved?\b",
    r"\bmeasured?\b",
    r"\bdetected?\b",
    r"\bfound that\b",
    r"\bresults show\b",
    r"\bdata indicate[sd]?\b",
    r"\bevidence shows?\b",
]


@dataclass
class ClassificationResult:
    """Result of claim classification."""

    claim_text: str
    label: ClaimLabel
    confidence: float
    matched_patterns: list[str]
    reason: str


def classify_claim_rule_based(claim_text: str) -> ClassificationResult:
    """Classify a claim using rule-based patterns.

    Args:
        claim_text: The claim text to classify.

    Returns:
        ClassificationResult with label and confidence.
    """
    claim_lower = claim_text.lower()
    matched_interp = []
    matched_fact = []

    # Check interpretation patterns
    for pattern in INTERPRETATION_PATTERNS:
        if re.search(pattern, claim_lower):
            matched_interp.append(pattern)

    # Check fact patterns
    for pattern in FACT_PATTERNS:
        if re.search(pattern, claim_lower):
            matched_fact.append(pattern)

    # Determine label
    if matched_interp and not matched_fact:
        # Clear interpretation
        confidence = min(0.9, 0.6 + len(matched_interp) * 0.1)
        return ClassificationResult(
            claim_text=claim_text,
            label=ClaimLabel.INTERPRETATION,
            confidence=confidence,
            matched_patterns=matched_interp,
            reason=f"Interpretation markers: {', '.join(matched_interp[:3])}",
        )

    elif matched_fact and not matched_interp:
        # Clear fact
        confidence = min(0.9, 0.6 + len(matched_fact) * 0.1)
        return ClassificationResult(
            claim_text=claim_text,
            label=ClaimLabel.FACT,
            confidence=confidence,
            matched_patterns=matched_fact,
            reason=f"Fact markers: {', '.join(matched_fact[:3])}",
        )

    elif matched_interp and matched_fact:
        # Mixed - lean toward interpretation (conservative)
        return ClassificationResult(
            claim_text=claim_text,
            label=ClaimLabel.INTERPRETATION,
            confidence=0.5,
            matched_patterns=matched_interp + matched_fact,
            reason="Mixed markers, conservative classification as interpretation",
        )

    else:
        # No clear markers
        return ClassificationResult(
            claim_text=claim_text,
            label=ClaimLabel.UNKNOWN,
            confidence=0.3,
            matched_patterns=[],
            reason="No clear markers found",
        )


def classify_claims(claims: list[str]) -> list[ClassificationResult]:
    """Classify multiple claims.

    Args:
        claims: List of claim texts.

    Returns:
        List of ClassificationResults.
    """
    return [classify_claim_rule_based(claim) for claim in claims]


def partition_claims(claims: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Partition claims into facts, interpretations, and unknown.

    Returns:
        (facts, interpretations, unknown)
    """
    facts = []
    interpretations = []
    unknown = []

    for claim in claims:
        result = classify_claim_rule_based(claim)
        if result.label == ClaimLabel.FACT:
            facts.append(claim)
        elif result.label in (ClaimLabel.INTERPRETATION, ClaimLabel.HYPOTHESIS):
            interpretations.append(claim)
        else:
            unknown.append(claim)

    return facts, interpretations, unknown