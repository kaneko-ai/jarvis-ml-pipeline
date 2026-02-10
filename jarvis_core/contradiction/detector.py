"""Contradiction Detector (Phase 28).

Detects logical contradictions between claims.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import List
from dataclasses import dataclass

try:
    import transformers as transformers
except Exception:  # pragma: no cover - compatibility for tests patching module attr

    class _TransformersShim:
        class _UnavailableSequenceModel:
            """Fallback object used when transformers is unavailable."""

            def __init__(self, model_name: str = "") -> None:
                self.model_name = model_name

        class AutoModelForSequenceClassification:
            @staticmethod
            def from_pretrained(
                *args: object, **kwargs: object
            ) -> "_TransformersShim._UnavailableSequenceModel":
                model_name = str(args[0]) if args else str(kwargs.get("model_name", ""))
                return _TransformersShim._UnavailableSequenceModel(model_name=model_name)

    transformers = _TransformersShim()

logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    """Represents a potential contradiction between two statements."""

    statement_a: str
    statement_b: str
    confidence: float
    reason: str


class ContradictionDetector:
    """Detects contradictions using heuristics or models."""

    def __init__(self, config: dict[str, object] | None = None) -> None:
        self.config: dict[str, object] = config or {}
        # Simple heuristic antonym pairs for smoke testing
        self.antonyms = [
            ("increase", "decrease"),
            ("positive", "negative"),
            ("effective", "ineffective"),
            ("safe", "dangerous"),
            ("significant", "insignificant"),
            ("true", "false"),
        ]

    def detect(self, claims: Sequence[str | Mapping[str, object]]) -> List[Contradiction]:
        """Detect contradictions within a list of claims."""
        contradictions = []

        for i, claim_a in enumerate(claims):
            for j, claim_b in enumerate(claims):
                if i >= j:
                    continue

                text_a = self._extract_text(claim_a)
                text_b = self._extract_text(claim_b)
                score = self._check_pair(text_a, text_b)
                if score > 0.5:
                    contradictions.append(
                        Contradiction(
                            statement_a=text_a,
                            statement_b=text_b,
                            confidence=score,
                            reason="Heuristic antonym match",
                        )
                    )

        return contradictions

    def _extract_text(self, claim: str | Mapping[str, object]) -> str:
        """Extract canonical text from claim-like objects."""
        if isinstance(claim, str):
            return claim
        if isinstance(claim, Mapping):
            text = claim.get("text")
            if isinstance(text, str):
                return text
            return str(text) if text is not None else ""
        return str(claim)

    def _check_pair(self, text_a: str, text_b: str) -> float:
        """Check a pair of texts for contradiction."""
        # Normalize
        a_lower = text_a.lower()
        b_lower = text_b.lower()

        # Heuristic: If sentences are very similar but contain antonyms
        # This is very simplistic but sufficient for Phase 28 smoke test

        # 1. Check for antonyms
        has_antonym = False
        for word1, word2 in self.antonyms:
            if (word1 in a_lower and word2 in b_lower) or (word2 in a_lower and word1 in b_lower):
                has_antonym = True
                break

        if has_antonym:
            # Check overlap to ensure context is similar
            words_a = set(a_lower.split())
            words_b = set(b_lower.split())
            overlap = len(words_a.intersection(words_b))
            union = len(words_a.union(words_b))
            jaccard = overlap / max(union, 1)

            if jaccard > 0.3:  # Arbitrary threshold for context similarity
                return 0.8

        return 0.0


def detect_contradiction(claims: Sequence[str]) -> List[Contradiction]:
    """Convenience function to detect contradictions."""
    detector = ContradictionDetector()
    return detector.detect(claims)
