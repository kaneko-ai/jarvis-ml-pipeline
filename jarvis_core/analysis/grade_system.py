"""GRADE Evidence Grading System for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 2.1: 証拠グレーディング
Implements GRADE-style evidence assessment with rule-based and LLM classifiers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class GRADELevel(Enum):
    """GRADE (Grading of Recommendations Assessment, Development and Evaluation) levels."""

    HIGH = "high"  # Further research unlikely to change confidence
    MODERATE = "moderate"  # Further research likely to change confidence
    LOW = "low"  # Further research very likely to change confidence
    VERY_LOW = "very_low"  # Very uncertain about the estimate


class StudyDesign(Enum):
    """Study design types for GRADE assessment."""

    RCT = "rct"  # Randomized controlled trial
    OBSERVATIONAL = "observational"  # Cohort, case-control
    CASE_SERIES = "case_series"  # Case series/reports
    EXPERT_OPINION = "expert_opinion"  # Expert opinion, narrative
    SYSTEMATIC_REVIEW = "systematic_review"  # Meta-analysis, SR
    UNKNOWN = "unknown"


class BiasRisk(Enum):
    """Risk of bias levels."""

    LOW = "low"
    SOME_CONCERNS = "some_concerns"
    HIGH = "high"


@dataclass
class GRADEAssessment:
    """Full GRADE assessment for a piece of evidence."""

    evidence_id: str
    claim_id: str

    # Initial level based on study design
    initial_level: GRADELevel
    study_design: StudyDesign

    # Downgrade factors
    risk_of_bias: BiasRisk = BiasRisk.LOW
    inconsistency: bool = False
    indirectness: bool = False
    imprecision: bool = False
    publication_bias: bool = False

    # Upgrade factors (for observational)
    large_effect: bool = False
    dose_response: bool = False
    confounders_reduced: bool = False

    # Final assessment
    final_level: GRADELevel = GRADELevel.MODERATE
    confidence_score: float = 0.5
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim_id": self.claim_id,
            "initial_level": self.initial_level.value,
            "final_level": self.final_level.value,
            "study_design": self.study_design.value,
            "risk_of_bias": self.risk_of_bias.value,
            "confidence_score": self.confidence_score,
            "explanation": self.explanation,
        }


class RuleBasedGrader:
    """Rule-based evidence grader using GRADE methodology.

    Implements heuristic-based grading without LLM.
    """

    # Keywords for study design detection
    STUDY_DESIGN_KEYWORDS = {
        StudyDesign.RCT: [
            "randomized",
            "randomised",
            "rct",
            "controlled trial",
            "double-blind",
            "placebo-controlled",
            "randomly assigned",
        ],
        StudyDesign.SYSTEMATIC_REVIEW: [
            "systematic review",
            "meta-analysis",
            "meta analysis",
            "pooled analysis",
            "cochrane",
        ],
        StudyDesign.OBSERVATIONAL: [
            "cohort",
            "case-control",
            "observational",
            "prospective",
            "retrospective",
            "follow-up",
            "longitudinal",
        ],
        StudyDesign.CASE_SERIES: ["case report", "case series", "case study", "single case"],
    }

    # Keywords for bias risk detection
    BIAS_KEYWORDS = {
        "high": ["limitation", "bias", "confound", "small sample", "underpowered"],
        "low": ["rigorous", "validated", "replicated", "large sample", "multicenter"],
    }

    def detect_study_design(self, text: str, metadata: dict | None = None) -> StudyDesign:
        """Detect study design from text and metadata."""
        text_lower = text.lower()

        for design, keywords in self.STUDY_DESIGN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return design

        # Check metadata for publication type
        if metadata:
            pub_type = metadata.get("publication_type", "").lower()
            if "clinical trial" in pub_type or "rct" in pub_type:
                return StudyDesign.RCT
            if "review" in pub_type:
                return StudyDesign.SYSTEMATIC_REVIEW

        return StudyDesign.UNKNOWN

    def assess_bias_risk(self, text: str, metadata: dict | None = None) -> BiasRisk:
        """Assess risk of bias from text."""
        text_lower = text.lower()

        high_count = sum(1 for kw in self.BIAS_KEYWORDS["high"] if kw in text_lower)
        low_count = sum(1 for kw in self.BIAS_KEYWORDS["low"] if kw in text_lower)

        if high_count > low_count + 1:
            return BiasRisk.HIGH
        elif low_count > high_count:
            return BiasRisk.LOW
        return BiasRisk.SOME_CONCERNS

    def get_initial_level(self, study_design: StudyDesign) -> GRADELevel:
        """Get initial GRADE level based on study design."""
        if study_design in [StudyDesign.RCT, StudyDesign.SYSTEMATIC_REVIEW]:
            return GRADELevel.HIGH
        elif study_design == StudyDesign.OBSERVATIONAL:
            return GRADELevel.LOW
        else:
            return GRADELevel.VERY_LOW

    def grade(
        self,
        evidence_id: str,
        claim_id: str,
        evidence_text: str,
        metadata: dict | None = None,
    ) -> GRADEAssessment:
        """Grade evidence using rule-based approach."""
        # Detect study design
        study_design = self.detect_study_design(evidence_text, metadata)
        initial_level = self.get_initial_level(study_design)

        # Assess bias risk
        bias_risk = self.assess_bias_risk(evidence_text, metadata)

        # Calculate downgrades
        downgrade_count = 0
        if bias_risk == BiasRisk.HIGH:
            downgrade_count += 1
        elif bias_risk == BiasRisk.SOME_CONCERNS:
            downgrade_count += 0.5

        # Determine final level
        levels = list(GRADELevel)
        initial_idx = levels.index(initial_level)
        final_idx = min(initial_idx + int(downgrade_count), len(levels) - 1)
        final_level = levels[final_idx]

        # Calculate confidence
        confidence = 1.0 - (final_idx * 0.25)

        return GRADEAssessment(
            evidence_id=evidence_id,
            claim_id=claim_id,
            initial_level=initial_level,
            study_design=study_design,
            risk_of_bias=bias_risk,
            final_level=final_level,
            confidence_score=confidence,
            explanation=f"Study design: {study_design.value}, Bias risk: {bias_risk.value}",
        )


class LLMGrader:
    """LLM-based evidence grader using local models.

    Uses Ollama/llama.cpp for more nuanced evidence assessment.
    """

    GRADE_PROMPT = """You are an expert evidence grader. Assess the following evidence for a scientific claim.

Claim: {claim}

Evidence: {evidence}

Evaluate and respond in JSON format:
{{
    "study_design": "rct|systematic_review|observational|case_series|expert_opinion",
    "confidence": 0.0-1.0,
    "grade": "high|moderate|low|very_low",
    "reasoning": "brief explanation"
}}

JSON Response:"""

    def __init__(self):
        self._router = None

    def _get_router(self):
        if self._router is None:
            try:
                from jarvis_core.llm.model_router import get_router

                self._router = get_router()
            except ImportError:
                logger.warning("Model router not available")
        return self._router

    def grade(
        self,
        evidence_id: str,
        claim_id: str,
        claim_text: str,
        evidence_text: str,
    ) -> GRADEAssessment | None:
        """Grade evidence using LLM."""
        router = self._get_router()
        if not router or not router.find_available_provider():
            return None

        prompt = self.GRADE_PROMPT.format(
            claim=claim_text[:500],
            evidence=evidence_text[:1000],
        )

        try:
            response = router.generate(
                prompt,
                max_tokens=256,
                temperature=0.1,
            )
            return self._parse_response(evidence_id, claim_id, response)
        except Exception as e:
            logger.error(f"LLM grading failed: {e}")
            return None

    def _parse_response(
        self,
        evidence_id: str,
        claim_id: str,
        response: str,
    ) -> GRADEAssessment | None:
        """Parse LLM response into assessment."""
        import json

        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])

                grade_map = {
                    "high": GRADELevel.HIGH,
                    "moderate": GRADELevel.MODERATE,
                    "low": GRADELevel.LOW,
                    "very_low": GRADELevel.VERY_LOW,
                }

                design_map = {
                    "rct": StudyDesign.RCT,
                    "systematic_review": StudyDesign.SYSTEMATIC_REVIEW,
                    "observational": StudyDesign.OBSERVATIONAL,
                    "case_series": StudyDesign.CASE_SERIES,
                    "expert_opinion": StudyDesign.EXPERT_OPINION,
                }

                return GRADEAssessment(
                    evidence_id=evidence_id,
                    claim_id=claim_id,
                    initial_level=GRADELevel.MODERATE,
                    study_design=design_map.get(data.get("study_design", ""), StudyDesign.UNKNOWN),
                    final_level=grade_map.get(data.get("grade", ""), GRADELevel.MODERATE),
                    confidence_score=float(data.get("confidence", 0.5)),
                    explanation=data.get("reasoning", ""),
                )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")

        return None


class EnsembleGrader:
    """Ensemble evidence grader combining rule-based and LLM approaches.

    Provides robust grading with fallback.
    """

    def __init__(
        self,
        use_llm: bool = True,
        llm_weight: float = 0.6,
        rule_weight: float = 0.4,
    ):
        self.use_llm = use_llm
        self.llm_weight = llm_weight
        self.rule_weight = rule_weight

        self.rule_grader = RuleBasedGrader()
        self.llm_grader = LLMGrader() if use_llm else None

    def grade(
        self,
        evidence_id: str,
        claim_id: str,
        claim_text: str,
        evidence_text: str,
        metadata: dict | None = None,
    ) -> GRADEAssessment:
        """Grade evidence using ensemble approach."""
        # Always run rule-based
        rule_result = self.rule_grader.grade(evidence_id, claim_id, evidence_text, metadata)

        # Try LLM if available
        llm_result = None
        if self.use_llm and self.llm_grader:
            llm_result = self.llm_grader.grade(evidence_id, claim_id, claim_text, evidence_text)

        # Combine results
        if llm_result:
            return self._combine_assessments(rule_result, llm_result)

        return rule_result

    def _combine_assessments(
        self,
        rule: GRADEAssessment,
        llm: GRADEAssessment,
    ) -> GRADEAssessment:
        """Combine rule-based and LLM assessments."""
        # Weighted confidence
        combined_confidence = (
            self.rule_weight * rule.confidence_score + self.llm_weight * llm.confidence_score
        )

        # Use LLM level if confidence higher, else rule
        if llm.confidence_score > rule.confidence_score:
            final_level = llm.final_level
            study_design = llm.study_design
            explanation = llm.explanation
        else:
            final_level = rule.final_level
            study_design = rule.study_design
            explanation = rule.explanation

        return GRADEAssessment(
            evidence_id=rule.evidence_id,
            claim_id=rule.claim_id,
            initial_level=rule.initial_level,
            study_design=study_design,
            risk_of_bias=rule.risk_of_bias,
            final_level=final_level,
            confidence_score=combined_confidence,
            explanation=f"Ensemble: {explanation}",
        )

    def grade_batch(
        self,
        evidence_list: list[dict],
        claims: list[dict],
    ) -> list[GRADEAssessment]:
        """Grade multiple evidence items."""
        # Build claim lookup
        claim_map = {c.get("claim_id", c.get("id")): c for c in claims}

        results = []
        for ev in evidence_list:
            evidence_id = ev.get("evidence_id", ev.get("id", ""))
            claim_id = ev.get("claim_id", "")
            claim = claim_map.get(claim_id, {})

            assessment = self.grade(
                evidence_id=evidence_id,
                claim_id=claim_id,
                claim_text=claim.get("claim_text", claim.get("text", "")),
                evidence_text=ev.get("text", ev.get("quote_span", "")),
                metadata=ev.get("metadata"),
            )
            results.append(assessment)

        return results


# Convenience function
def grade_evidence_with_grade(
    evidence_list: list[dict],
    claims: list[dict],
    use_llm: bool = True,
) -> tuple[list[GRADEAssessment], dict[str, Any]]:
    """Grade evidence using GRADE methodology.

    Args:
        evidence_list: List of evidence dictionaries.
        claims: List of claim dictionaries.
        use_llm: Whether to use LLM for grading.

    Returns:
        Tuple of (assessments, summary_stats).
    """
    grader = EnsembleGrader(use_llm=use_llm)
    assessments = grader.grade_batch(evidence_list, claims)

    # Calculate statistics
    level_counts = {level.value: 0 for level in GRADELevel}
    total_confidence = 0.0

    for a in assessments:
        level_counts[a.final_level.value] += 1
        total_confidence += a.confidence_score

    avg_confidence = total_confidence / len(assessments) if assessments else 0.0

    stats = {
        "total_evidence": len(assessments),
        "level_distribution": level_counts,
        "average_confidence": avg_confidence,
        "high_quality_count": level_counts["high"] + level_counts["moderate"],
    }

    return assessments, stats
