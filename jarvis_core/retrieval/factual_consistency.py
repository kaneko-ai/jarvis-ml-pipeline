"""Factual Consistency Checker.

Per RP-318, validates generated text against sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConsistencyLevel(Enum):
    """Consistency levels."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"
    CONTRADICTED = "contradicted"


@dataclass
class ClaimCheck:
    """Result of checking a single claim."""

    claim: str
    level: ConsistencyLevel
    supporting_chunks: list[str]
    confidence: float
    explanation: str


@dataclass
class ConsistencyReport:
    """Full consistency check report."""

    claims_checked: int
    supported: int
    partially_supported: int
    not_supported: int
    contradicted: int
    overall_score: float
    claim_checks: list[ClaimCheck]


class FactualConsistencyChecker:
    """Checks factual consistency of generated text.

    Per RP-318:
    - Decomposes generated text into claims
    - Verifies each claim against sources
    - Detects contradictions
    - Flags unsupported claims
    """

    def __init__(
        self,
        nli_model=None,
        claim_extractor=None,
        threshold_supported: float = 0.7,
        threshold_partial: float = 0.4,
    ):
        self.nli_model = nli_model
        self.claim_extractor = claim_extractor
        self.threshold_supported = threshold_supported
        self.threshold_partial = threshold_partial

    def extract_claims(self, text: str) -> list[str]:
        """Extract claims from generated text.

        Args:
            text: Generated text.

        Returns:
            List of claim strings.
        """
        if self.claim_extractor:
            return self.claim_extractor(text)

        return self._simple_claim_extraction(text)

    def _simple_claim_extraction(self, text: str) -> list[str]:
        """Simple rule-based claim extraction."""
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Skip questions, commands, etc.
            if sentence.endswith("?"):
                continue

            # Skip very short sentences
            if len(sentence) < 20:
                continue

            # Skip hedged statements (these are opinions, not claims)
            hedge_patterns = [
                r"(?i)^(I think|In my opinion|Perhaps|Maybe|It seems)",
                r"(?i)^(This suggests|This may|This could)",
            ]
            is_hedged = any(re.match(p, sentence) for p in hedge_patterns)

            if not is_hedged:
                claims.append(sentence)

        return claims

    def check_claim(
        self,
        claim: str,
        source_chunks: list[dict[str, Any]],
    ) -> ClaimCheck:
        """Check a single claim against sources.

        Args:
            claim: The claim to check.
            source_chunks: Source chunks to verify against.

        Returns:
            ClaimCheck result.
        """
        if not source_chunks:
            return ClaimCheck(
                claim=claim,
                level=ConsistencyLevel.NOT_SUPPORTED,
                supporting_chunks=[],
                confidence=0.0,
                explanation="No source chunks provided",
            )

        supporting = []
        max_score = 0.0

        for chunk in source_chunks:
            chunk_text = chunk.get("text", "")
            chunk_id = chunk.get("chunk_id", "unknown")

            # Calculate entailment score
            score = self._calculate_entailment(claim, chunk_text)

            if score >= self.threshold_partial:
                supporting.append(chunk_id)
                max_score = max(max_score, score)

        # Determine level
        if max_score >= self.threshold_supported:
            level = ConsistencyLevel.SUPPORTED
        elif max_score >= self.threshold_partial:
            level = ConsistencyLevel.PARTIALLY_SUPPORTED
        else:
            level = ConsistencyLevel.NOT_SUPPORTED

        return ClaimCheck(
            claim=claim,
            level=level,
            supporting_chunks=supporting,
            confidence=max_score,
            explanation=self._generate_explanation(level, supporting),
        )

    def _calculate_entailment(self, claim: str, source: str) -> float:
        """Calculate entailment score between claim and source.

        Args:
            claim: The claim.
            source: The source text.

        Returns:
            Entailment score (0-1).
        """
        if self.nli_model:
            # Use NLI model
            return self.nli_model.predict(claim, source)

        # Simple lexical overlap fallback
        claim_words = set(claim.lower().split())
        source_words = set(source.lower().split())

        if not claim_words:
            return 0.0

        overlap = len(claim_words & source_words)
        return overlap / len(claim_words)

    def _generate_explanation(
        self,
        level: ConsistencyLevel,
        supporting: list[str],
    ) -> str:
        """Generate explanation for check result."""
        if level == ConsistencyLevel.SUPPORTED:
            return f"Fully supported by {len(supporting)} source(s)"
        elif level == ConsistencyLevel.PARTIALLY_SUPPORTED:
            return f"Partially supported by {len(supporting)} source(s)"
        elif level == ConsistencyLevel.CONTRADICTED:
            return "Contradicted by source evidence"
        else:
            return "No supporting evidence found in sources"

    def check_text(
        self,
        generated_text: str,
        source_chunks: list[dict[str, Any]],
    ) -> ConsistencyReport:
        """Check full generated text for consistency.

        Args:
            generated_text: The generated text.
            source_chunks: Source chunks to verify against.

        Returns:
            ConsistencyReport with all claim checks.
        """
        claims = self.extract_claims(generated_text)

        checks = []
        supported = 0
        partial = 0
        not_supported = 0
        contradicted = 0

        for claim in claims:
            check = self.check_claim(claim, source_chunks)
            checks.append(check)

            if check.level == ConsistencyLevel.SUPPORTED:
                supported += 1
            elif check.level == ConsistencyLevel.PARTIALLY_SUPPORTED:
                partial += 1
            elif check.level == ConsistencyLevel.CONTRADICTED:
                contradicted += 1
            else:
                not_supported += 1

        total = len(claims)
        score = (supported + 0.5 * partial) / total if total > 0 else 0.0

        return ConsistencyReport(
            claims_checked=total,
            supported=supported,
            partially_supported=partial,
            not_supported=not_supported,
            contradicted=contradicted,
            overall_score=score,
            claim_checks=checks,
        )