"""Contradiction Resolution Module.

Suggests resolutions for detected contradictions.
Per JARVIS_COMPLETION_INSTRUCTION Task 2.3.1
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResolutionStrategy(Enum):
    """Strategies for resolving contradictions."""

    METHODOLOGY = "methodology"  # Different methods
    POPULATION = "population"  # Different study populations
    TIMEFRAME = "timeframe"  # Different time periods
    MEASURE = "measure"  # Different measurements
    CONTEXT = "context"  # Different contexts
    DEFINITION = "definition"  # Different definitions
    UNKNOWN = "unknown"


@dataclass
class ResolutionSuggestion:
    """A suggested resolution for a contradiction."""

    strategy: ResolutionStrategy
    explanation: str
    confidence: float
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "evidence_for": self.evidence_for,
            "evidence_against": self.evidence_against,
            "recommended_action": self.recommended_action,
        }


class ContradictionResolver:
    """Resolves contradictions using rule-based and LLM methods."""

    def __init__(self, use_llm: bool = True):
        """Initialize resolver.

        Args:
            use_llm: Whether to use LLM for resolution suggestions
        """
        self._use_llm = use_llm

    def suggest_resolution(
        self,
        claim_a: str,
        claim_b: str,
        context_a: str = "",
        context_b: str = "",
    ) -> ResolutionSuggestion:
        """Suggest resolution for contradicting claims.

        Args:
            claim_a: First claim text
            claim_b: Second claim text
            context_a: Context for first claim
            context_b: Context for second claim

        Returns:
            ResolutionSuggestion object
        """
        # Try rule-based first
        rule_strategy = self._rule_based_suggestion(claim_a, claim_b)

        if rule_strategy and rule_strategy != ResolutionStrategy.UNKNOWN:
            explanation = self._generate_explanation(rule_strategy, claim_a, claim_b)
            return ResolutionSuggestion(
                strategy=rule_strategy,
                explanation=explanation,
                confidence=0.7,
                recommended_action=self._get_recommended_action(rule_strategy),
            )

        # Use LLM if enabled and rules didn't match
        if self._use_llm:
            return self._llm_suggest(claim_a, claim_b, context_a, context_b)

        return ResolutionSuggestion(
            strategy=ResolutionStrategy.UNKNOWN,
            explanation="Unable to determine resolution strategy",
            confidence=0.3,
            recommended_action="Manually review both claims and their contexts",
        )

    def _rule_based_suggestion(self, claim_a: str, claim_b: str) -> ResolutionStrategy | None:
        """Apply rule-based heuristics."""
        text_a = claim_a.lower()
        text_b = claim_b.lower()
        combined = text_a + " " + text_b

        # Numeric differences -> measurement
        if re.search(r"\d+%", text_a) and re.search(r"\d+%", text_b):
            return ResolutionStrategy.MEASURE

        # Time expressions -> timeframe
        time_patterns = [r"\d{4}", r"year", r"month", r"recent", r"during"]
        if any(re.search(p, combined) for p in time_patterns):
            return ResolutionStrategy.TIMEFRAME

        # Population expressions -> population
        pop_patterns = [
            r"patients?",
            r"subjects?",
            r"participants?",
            r"adults?",
            r"children",
            r"elderly",
        ]
        if any(re.search(p, combined) for p in pop_patterns):
            return ResolutionStrategy.POPULATION

        # Method expressions -> methodology
        method_patterns = [r"method", r"approach", r"technique", r"protocol", r"procedure"]
        if any(re.search(p, combined) for p in method_patterns):
            return ResolutionStrategy.METHODOLOGY

        return None

    def _generate_explanation(
        self, strategy: ResolutionStrategy, claim_a: str, claim_b: str
    ) -> str:
        """Generate explanation for resolution strategy."""
        explanations = {
            ResolutionStrategy.METHODOLOGY: "The claims may differ due to different research methodologies or experimental approaches.",
            ResolutionStrategy.POPULATION: "The discrepancy could arise from studying different populations or patient groups.",
            ResolutionStrategy.TIMEFRAME: "The findings may reflect changes over time or different study periods.",
            ResolutionStrategy.MEASURE: "Different measurement methods or metrics may explain the numerical differences.",
            ResolutionStrategy.CONTEXT: "The context or setting of each study may account for the difference.",
            ResolutionStrategy.DEFINITION: "Different operational definitions may lead to apparent contradiction.",
        }
        return explanations.get(strategy, "Further investigation needed.")

    def _get_recommended_action(self, strategy: ResolutionStrategy) -> str:
        """Get recommended action for resolution strategy."""
        actions = {
            ResolutionStrategy.METHODOLOGY: "Compare methodologies and determine which is more appropriate for your use case.",
            ResolutionStrategy.POPULATION: "Consider which population is more relevant to your research question.",
            ResolutionStrategy.TIMEFRAME: "Prefer more recent findings unless historical context is important.",
            ResolutionStrategy.MEASURE: "Standardize measurements or report both findings with their respective metrics.",
            ResolutionStrategy.CONTEXT: "Explicitly state the applicable context for each finding.",
            ResolutionStrategy.DEFINITION: "Clarify definitions and map to your operational definitions.",
        }
        return actions.get(strategy, "Conduct deeper analysis of both sources.")

    def _llm_suggest(
        self,
        claim_a: str,
        claim_b: str,
        context_a: str,
        context_b: str,
    ) -> ResolutionSuggestion:
        """Use LLM for resolution suggestion."""
        try:
            from jarvis_core.llm import get_router

            router = get_router()

            prompt = f"""Analyze the contradiction between these claims:

Claim A: {claim_a}
Context A: {context_a}

Claim B: {claim_b}
Context B: {context_b}

Suggest how this contradiction might be resolved. Consider different methodologies, populations, timeframes, or contexts.

Respond briefly with the most likely resolution strategy and explanation."""

            response = router.generate(prompt, max_tokens=200)

            # Parse response (simplified)
            return ResolutionSuggestion(
                strategy=ResolutionStrategy.UNKNOWN,  # Would parse from response
                explanation=response[:500] if response else "LLM analysis unavailable",
                confidence=0.6,
                recommended_action="Review LLM analysis and verify with original sources",
            )
        except Exception:
            return ResolutionSuggestion(
                strategy=ResolutionStrategy.UNKNOWN,
                explanation="LLM analysis unavailable",
                confidence=0.3,
                recommended_action="Manually review both claims",
            )