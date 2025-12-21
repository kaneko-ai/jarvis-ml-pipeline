"""Negative Results Vault.

Per Ψ-2, this stores and analyzes failed experiments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class NegativeResult:
    """A negative/failed result entry."""

    id: str
    hypothesis: str
    experiment: str
    outcome: str
    failure_type: str  # technical, biological, conceptual
    date: datetime = field(default_factory=datetime.now)
    reuse_potential: float = 0.5

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hypothesis": self.hypothesis,
            "experiment": self.experiment,
            "outcome": self.outcome,
            "failure_type": self.failure_type,
            "date": self.date.isoformat(),
            "reuse_potential": self.reuse_potential,
        }


class NegativeResultsVault:
    """Storage for negative results."""

    def __init__(self):
        self.results: List[NegativeResult] = []

    def add(self, result: NegativeResult) -> None:
        self.results.append(result)

    def find_similar_failures(self, hypothesis: str) -> List[NegativeResult]:
        """Find similar past failures."""
        hypothesis_lower = hypothesis.lower()
        return [
            r for r in self.results
            if any(word in r.hypothesis.lower() for word in hypothesis_lower.split()[:3])
        ]

    def get_failure_patterns(self) -> Dict[str, int]:
        """Get failure type distribution."""
        patterns = {}
        for r in self.results:
            patterns[r.failure_type] = patterns.get(r.failure_type, 0) + 1
        return patterns

    def suggest_reuse(self, new_hypothesis: str) -> List[dict]:
        """Suggest ways to reuse negative results."""
        similar = self.find_similar_failures(new_hypothesis)
        suggestions = []

        for r in similar:
            if r.reuse_potential > 0.3:
                suggestions.append({
                    "original": r.hypothesis[:50],
                    "reuse_hint": f"過去の{r.failure_type}失敗から学習可能",
                    "potential": r.reuse_potential,
                })

        return suggestions


def analyze_negative_results(results: List[NegativeResult]) -> dict:
    """Analyze patterns in negative results."""
    if not results:
        return {"patterns": {}, "total": 0}

    patterns = {}
    for r in results:
        patterns[r.failure_type] = patterns.get(r.failure_type, 0) + 1

    dominant_failure = max(patterns.items(), key=lambda x: x[1])[0] if patterns else None

    return {
        "failure_patterns": patterns,
        "total": len(results),
        "dominant_failure_type": dominant_failure,
        "reuse_potential_avg": round(sum(r.reuse_potential for r in results) / len(results), 2),
    }
