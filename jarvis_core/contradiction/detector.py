"""Contradiction Detector (B-2 enhanced).

Detects contradictions between paper claims using:
  1. LLM-based semantic analysis (Gemini API) - when --use-llm is set
  2. Keyword heuristic fallback (original method)
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Sequence

from jarvis_core.contradiction.schema import (
    Claim,
    ClaimPair,
    ContradictionResult,
    ContradictionType,
)

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """Detects contradictions between pairs of claims.

    B-2: Added LLM-based detection via Gemini API.
    """

    def __init__(self, use_llm: bool = False, provider: str = "gemini"):
        self.use_llm = use_llm
        self.provider = provider
        self._llm = None
        self.antonyms = [
            ("increase", "decrease"),
            ("positive", "negative"),
            ("effective", "ineffective"),
            ("safe", "dangerous"),
            ("significant", "insignificant"),
            ("beneficial", "harmful"),
            ("promote", "inhibit"),
            ("activate", "suppress"),
            ("upregulate", "downregulate"),
            ("enhance", "reduce"),
        ]

    def _get_llm(self):
        """Lazy-init LLM client."""
        if self._llm is None and self.use_llm:
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass
            try:
                from jarvis_core.llm import LLMClient
                self._llm = LLMClient(provider=self.provider)
            except Exception as e:
                logger.warning(f"LLM init failed: {e}. Falling back to heuristic.")
                self.use_llm = False
        return self._llm

    def detect(self, claim_a: Claim, claim_b: Claim) -> ContradictionResult:
        """Detect contradiction between two claims.

        Args:
            claim_a: First claim.
            claim_b: Second claim.

        Returns:
            ContradictionResult with type, confidence, and explanation.
        """
        pair = ClaimPair(claim_a=claim_a, claim_b=claim_b)

        if self.use_llm:
            llm = self._get_llm()
            if llm:
                return self._detect_llm(llm, pair)

        return self._detect_heuristic(pair)

    def detect_batch(self, claims: Sequence[Claim]) -> list[ContradictionResult]:
        """Detect contradictions among all pairs of claims.

        Args:
            claims: List of claims to compare pairwise.

        Returns:
            List of ContradictionResult for pairs with contradictions.
        """
        results = []
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                result = self.detect(claims[i], claims[j])
                if result.is_contradictory:
                    results.append(result)
        return results

    def _detect_llm(self, llm, pair: ClaimPair) -> ContradictionResult:
        """Detect contradiction using LLM (Gemini)."""
        from jarvis_core.llm import Message

        text_a = pair.claim_a.text[:500]
        text_b = pair.claim_b.text[:500]
        title_a = pair.claim_a.paper_id
        title_b = pair.claim_b.paper_id

        system_prompt = (
            "You are a scientific contradiction detector.\n"
            "Given two paper abstracts, determine if they contain contradictory findings.\n\n"
            "Contradiction types:\n"
            "- direct: A says X, B says not-X\n"
            "- quantitative: Conflicting numeric results\n"
            "- methodological: Different methods lead to opposite conclusions\n"
            "- partial: Partially contradictory findings\n"
            "- none: No contradiction\n\n"
            "Output ONLY a JSON object:\n"
            '{"type": "direct|quantitative|methodological|partial|none", '
            '"confidence": 0.0-1.0, "explanation": "brief reason"}'
        )

        user_prompt = (
            f"Paper A ({title_a}):\n{text_a}\n\n"
            f"Paper B ({title_b}):\n{text_b}"
        )

        try:
            raw = llm.chat([
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ])
            raw_clean = raw.strip()
            if raw_clean.startswith("```"):
                raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_clean)
                raw_clean = re.sub(r"\s*```$", "", raw_clean)

            parsed = json.loads(raw_clean)

            type_map = {
                "direct": ContradictionType.DIRECT,
                "quantitative": ContradictionType.QUANTITATIVE,
                "methodological": ContradictionType.METHODOLOGICAL,
                "partial": ContradictionType.PARTIAL,
                "temporal": ContradictionType.TEMPORAL,
                "none": ContradictionType.NONE,
            }
            ctype = type_map.get(parsed.get("type", "none"), ContradictionType.NONE)
            confidence = float(parsed.get("confidence", 0.0))
            explanation = parsed.get("explanation", "")

            return ContradictionResult(
                claim_pair=pair,
                contradiction_type=ctype,
                confidence=confidence,
                explanation=explanation,
                evidence=[f"LLM ({self.provider}) classification"],
            )
        except Exception as e:
            logger.warning(f"LLM contradiction detection failed: {e}")
            return self._detect_heuristic(pair)

    def _detect_heuristic(self, pair: ClaimPair) -> ContradictionResult:
        """Detect contradiction using keyword heuristics."""
        text_a = pair.claim_a.text.lower()
        text_b = pair.claim_b.text.lower()

        # Check for antonym pairs
        has_antonym = False
        matched_pair = None
        for word1, word2 in self.antonyms:
            if (word1 in text_a and word2 in text_b) or (word2 in text_a and word1 in text_b):
                has_antonym = True
                matched_pair = (word1, word2)
                break

        if has_antonym:
            # Check context overlap (Jaccard similarity)
            words_a = set(text_a.split())
            words_b = set(text_b.split())
            overlap = len(words_a & words_b)
            union = len(words_a | words_b)
            jaccard = overlap / max(union, 1)

            if jaccard > 0.15:
                return ContradictionResult(
                    claim_pair=pair,
                    contradiction_type=ContradictionType.DIRECT,
                    confidence=min(0.7, 0.4 + jaccard),
                    explanation=f"Antonym pair ({matched_pair[0]}/{matched_pair[1]}) with topic overlap ({jaccard:.2f})",
                    evidence=[f"Antonym: {matched_pair[0]} vs {matched_pair[1]}"],
                )

        return ContradictionResult(
            claim_pair=pair,
            contradiction_type=ContradictionType.NONE,
            confidence=0.1,
            explanation="No contradiction indicators found",
        )


def detect_contradiction(claims: Sequence[Claim], use_llm: bool = False) -> list[ContradictionResult]:
    """Convenience function to detect contradictions among claims."""
    detector = ContradictionDetector(use_llm=use_llm)
    return detector.detect_batch(list(claims))
