"""Citation Stance Analyzer for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 2.2: 引用分析
Classifies citation stance (support/contrast/neutral) locally.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CitationStance(Enum):
    """Citation stance categories."""

    SUPPORTS = "supports"  # Evidence supports the claim
    CONTRADICTS = "contradicts"  # Evidence contradicts the claim
    NEUTRAL = "neutral"  # No clear stance
    EXTENDS = "extends"  # Builds upon without support/contradiction
    UNRELATED = "unrelated"  # Not related to the claim


@dataclass
class StanceResult:
    """Result of stance classification."""

    claim_id: str
    evidence_id: str
    stance: CitationStance
    confidence: float
    explanation: str
    cue_words: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "evidence_id": self.evidence_id,
            "stance": self.stance.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "cue_words": self.cue_words,
        }


class RuleBasedStanceClassifier:
    """Rule-based stance classifier using linguistic cues.

    Fast and deterministic, no external dependencies.
    """

    # Linguistic cue word patterns
    SUPPORT_CUES = [
        r"\bconfirm(s|ed|ing)?\b",
        r"\bsupport(s|ed|ing)?\b",
        r"\bconsistent with\b",
        r"\bin agreement\b",
        r"\bcorroborate(s|d)?\b",
        r"\breplicate(s|d)?\b",
        r"\bvalidate(s|d)?\b",
        r"\balign(s|ed)? with\b",
        r"\bdemonstrate(s|d)?\b",
        r"\bshow(n|s|ed)?\b",
        r"\bevidence for\b",
        r"\bpositive correlation\b",
        r"\bsimilar(ly)?\b",
        r"\bas expected\b",
    ]

    CONTRADICT_CUES = [
        r"\bcontradict(s|ed|ing)?\b",
        r"\bconflict(s|ed|ing)?\b",
        r"\binconsistent\b",
        r"\boppos(e|es|ed|ing)\b",
        r"\bcontrary to\b",
        r"\bchallenge(s|d)?\b",
        r"\brefute(s|d)?\b",
        r"\bdisagree\b",
        r"\bunlike\b",
        r"\bfail(s|ed)? to\b",
        r"\bdid not find\b",
        r"\bnot support\b",
        r"\bnegative correlation\b",
        r"\bhowever\b",
        r"\balthough\b",
        r"\bdespite\b",
    ]

    EXTEND_CUES = [
        r"\bextend(s|ed|ing)?\b",
        r"\bbuild(s|ing)? on\b",
        r"\bfurther(more)?\b",
        r"\badditionally\b",
        r"\bmoreover\b",
        r"\bexpand(s|ed|ing)?\b",
        r"\bbroaden(s|ed|ing)?\b",
    ]

    def classify(
        self,
        claim_text: str,
        evidence_text: str,
        claim_id: str = "",
        evidence_id: str = "",
    ) -> StanceResult:
        """Classify stance between claim and evidence."""
        text_lower = evidence_text.lower()
        claim_lower = claim_text.lower()

        # Find cue words
        support_matches = self._find_cues(text_lower, self.SUPPORT_CUES)
        contradict_matches = self._find_cues(text_lower, self.CONTRADICT_CUES)
        extend_matches = self._find_cues(text_lower, self.EXTEND_CUES)

        # Scoring
        support_score = len(support_matches) * 1.0
        contradict_score = len(contradict_matches) * 1.5  # Weight contradictions higher
        extend_score = len(extend_matches) * 0.5

        # Check for negation of support
        if self._has_negated_support(text_lower):
            support_score -= 1.0
            contradict_score += 0.5

        # Determine stance
        total = support_score + contradict_score + extend_score + 0.1

        if contradict_score > support_score and contradict_score >= 1.0:
            stance = CitationStance.CONTRADICTS
            confidence = min(0.9, 0.5 + contradict_score / (total * 2))
            cues = contradict_matches
        elif support_score > contradict_score and support_score >= 0.5:
            stance = CitationStance.SUPPORTS
            confidence = min(0.9, 0.5 + support_score / (total * 2))
            cues = support_matches
        elif extend_score > 0:
            stance = CitationStance.EXTENDS
            confidence = min(0.8, 0.4 + extend_score / total)
            cues = extend_matches
        else:
            stance = CitationStance.NEUTRAL
            confidence = 0.3
            cues = []

        return StanceResult(
            claim_id=claim_id,
            evidence_id=evidence_id,
            stance=stance,
            confidence=confidence,
            explanation=f"Found cues: {', '.join(cues[:3])}",
            cue_words=cues,
        )

    def _find_cues(self, text: str, patterns: list[str]) -> list[str]:
        """Find matching cue words."""
        matches = []
        for pattern in patterns:
            if re.search(pattern, text):
                # Extract the actual word
                match = re.search(pattern, text)
                if match:
                    matches.append(match.group())
        return matches

    def _has_negated_support(self, text: str) -> bool:
        """Check for negated support phrases."""
        negation_patterns = [
            r"\bnot support\b",
            r"\bdoes not confirm\b",
            r"\bfailed to replicate\b",
            r"\bunable to validate\b",
            r"\bno evidence\b",
        ]
        for pattern in negation_patterns:
            if re.search(pattern, text):
                return True
        return False


class LLMStanceClassifier:
    """LLM-based stance classifier using local models."""

    STANCE_PROMPT = """Analyze the relationship between this claim and evidence.

CLAIM: {claim}

EVIDENCE: {evidence}

What is the stance of the evidence toward the claim?
Respond with ONE word: SUPPORTS, CONTRADICTS, NEUTRAL, or EXTENDS

Answer:"""

    def __init__(self):
        self._router = None

    def _get_router(self):
        if self._router is None:
            try:
                from jarvis_core.llm.model_router import get_router

                self._router = get_router()
            except ImportError:
                pass
        return self._router

    def classify(
        self,
        claim_text: str,
        evidence_text: str,
        claim_id: str = "",
        evidence_id: str = "",
    ) -> StanceResult | None:
        """Classify stance using LLM."""
        router = self._get_router()
        if not router or not router.find_available_provider():
            return None

        prompt = self.STANCE_PROMPT.format(
            claim=claim_text[:300],
            evidence=evidence_text[:500],
        )

        try:
            response = (
                router.generate(
                    prompt,
                    max_tokens=20,
                    temperature=0.0,
                )
                .strip()
                .upper()
            )

            if "SUPPORT" in response:
                stance = CitationStance.SUPPORTS
            elif "CONTRADICT" in response:
                stance = CitationStance.CONTRADICTS
            elif "EXTEND" in response:
                stance = CitationStance.EXTENDS
            else:
                stance = CitationStance.NEUTRAL

            return StanceResult(
                claim_id=claim_id,
                evidence_id=evidence_id,
                stance=stance,
                confidence=0.7,
                explanation=f"LLM classified as {stance.value}",
                cue_words=[],
            )
        except Exception as e:
            logger.error(f"LLM stance classification failed: {e}")
            return None


class EnsembleStanceClassifier:
    """Ensemble classifier combining rule-based and LLM approaches."""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.rule_classifier = RuleBasedStanceClassifier()
        self.llm_classifier = LLMStanceClassifier() if use_llm else None

    def classify(
        self,
        claim_text: str,
        evidence_text: str,
        claim_id: str = "",
        evidence_id: str = "",
    ) -> StanceResult:
        """Classify using ensemble."""
        rule_result = self.rule_classifier.classify(
            claim_text, evidence_text, claim_id, evidence_id
        )

        if not self.use_llm or not self.llm_classifier:
            return rule_result

        llm_result = self.llm_classifier.classify(claim_text, evidence_text, claim_id, evidence_id)

        if not llm_result:
            return rule_result

        # If they agree, boost confidence
        if rule_result.stance == llm_result.stance:
            return StanceResult(
                claim_id=claim_id,
                evidence_id=evidence_id,
                stance=rule_result.stance,
                confidence=min(0.95, rule_result.confidence + 0.1),
                explanation=f"Both classifiers agree: {rule_result.stance.value}",
                cue_words=rule_result.cue_words,
            )

        # If they disagree, prefer LLM for high-confidence, else rule-based
        if llm_result.confidence > rule_result.confidence:
            return llm_result
        return rule_result

    def classify_batch(
        self,
        pairs: list[tuple[str, str, str, str]],  # (claim, evidence, claim_id, evidence_id)
    ) -> list[StanceResult]:
        """Classify multiple claim-evidence pairs."""
        return [
            self.classify(claim, evidence, claim_id, ev_id)
            for claim, evidence, claim_id, ev_id in pairs
        ]


def analyze_citations(
    claims: list[dict],
    evidence_list: list[dict],
    use_llm: bool = True,
) -> tuple[list[StanceResult], dict[str, Any]]:
    """Analyze citation stances for all claim-evidence pairs.

    Args:
        claims: List of claim dictionaries.
        evidence_list: List of evidence dictionaries.
        use_llm: Whether to use LLM classifier.

    Returns:
        Tuple of (results, summary_stats).
    """
    classifier = EnsembleStanceClassifier(use_llm=use_llm)

    # Build claim lookup
    claim_map = {c.get("claim_id", c.get("id")): c for c in claims}

    results = []
    for ev in evidence_list:
        claim_id = ev.get("claim_id", "")
        claim = claim_map.get(claim_id, {})

        result = classifier.classify(
            claim_text=claim.get("claim_text", claim.get("text", "")),
            evidence_text=ev.get("text", ev.get("quote_span", "")),
            claim_id=claim_id,
            evidence_id=ev.get("evidence_id", ev.get("id", "")),
        )
        results.append(result)

    # Calculate statistics
    stance_counts = {s.value: 0 for s in CitationStance}
    for r in results:
        stance_counts[r.stance.value] += 1

    stats = {
        "total_analyzed": len(results),
        "stance_distribution": stance_counts,
        "support_rate": stance_counts["supports"] / len(results) if results else 0,
        "contradiction_rate": stance_counts["contradicts"] / len(results) if results else 0,
    }

    return results, stats
