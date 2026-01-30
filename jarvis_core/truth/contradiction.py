"""Contradiction Detector.

Per V4-T04, this detects potential contradictions between facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.schema import Fact


# Antonym patterns
ANTONYM_PATTERNS = [
    ("increase", "decrease"),
    ("activate", "inhibit"),
    ("promote", "suppress"),
    ("positive", "negative"),
    ("high", "low"),
    ("upregulate", "downregulate"),
    ("induce", "prevent"),
    ("enhance", "reduce"),
]


@dataclass
class ContradictionResult:
    """Result of contradiction detection."""

    fact1: str
    fact2: str
    contradiction_type: str
    confidence: float
    shared_concept: str

    def to_dict(self) -> dict:
        return {
            "fact1": self.fact1[:100],
            "fact2": self.fact2[:100],
            "contradiction_type": self.contradiction_type,
            "confidence": self.confidence,
            "shared_concept": self.shared_concept,
        }


def find_shared_concepts(text1: str, text2: str) -> list[str]:
    """Find shared concepts between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Filter stopwords
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "and",
        "that",
        "this",
    }
    shared = words1 & words2 - stopwords

    # Keep only substantial words
    return [w for w in shared if len(w) > 3]


def check_antonym_pattern(text1: str, text2: str) -> tuple[bool, str]:
    """Check if texts contain antonym patterns."""
    text1_lower = text1.lower()
    text2_lower = text2.lower()

    for word1, word2 in ANTONYM_PATTERNS:
        if word1 in text1_lower and word2 in text2_lower:
            return True, f"{word1} vs {word2}"
        if word2 in text1_lower and word1 in text2_lower:
            return True, f"{word2} vs {word1}"

    return False, ""


def detect_contradictions(
    facts: list[Fact],
) -> list[ContradictionResult]:
    """Detect potential contradictions between facts.

    Args:
        facts: List of facts to check.

    Returns:
        List of potential contradictions.

    Note:
        Results are "potential" contradictions, not definitive.
    """
    if len(facts) < 2:
        return []

    contradictions = []

    for i, fact1 in enumerate(facts):
        for fact2 in facts[i + 1 :]:
            # Check for shared concepts
            shared = find_shared_concepts(fact1.statement, fact2.statement)

            if not shared:
                continue

            # Check for antonym pattern
            has_antonym, pattern = check_antonym_pattern(
                fact1.statement,
                fact2.statement,
            )

            if has_antonym:
                contradictions.append(
                    ContradictionResult(
                        fact1=fact1.statement,
                        fact2=fact2.statement,
                        contradiction_type=f"antonym_pattern: {pattern}",
                        confidence=0.5,  # Not definitive
                        shared_concept=shared[0] if shared else "",
                    )
                )

    return contradictions


def summarize_contradictions(results: list[ContradictionResult]) -> str:
    """Generate human-readable summary of contradictions."""
    if not results:
        return "矛盾の可能性は検出されませんでした。"

    lines = ["## 潜在的な矛盾の可能性", ""]
    lines.append(f"検出数: {len(results)}")
    lines.append("")

    for i, r in enumerate(results[:5], 1):
        lines.append(f"### {i}. {r.shared_concept}に関する矛盾の可能性")
        lines.append(f"- Fact A: {r.fact1[:80]}...")
        lines.append(f"- Fact B: {r.fact2[:80]}...")
        lines.append(f"- タイプ: {r.contradiction_type}")
        lines.append("")

    lines.append("> 注: これらは潜在的な矛盾であり、確定ではありません。")

    return "\n".join(lines)