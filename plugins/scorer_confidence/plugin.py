"""
JARVIS Scoring Plugin - Importance, Confidence, ROI Scoring

論文・Claimの多軸スコアリング。
全スコアにevidence_links必須。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, Claim, EvidenceLink, Score, RuntimeConfig, TaskContext
)


@dataclass
class ScoringResult:
    """スコアリング結果."""
    score_name: str
    value: float  # 0-1
    explanation: str
    factors: Dict[str, float]
    evidence: List[EvidenceLink] = field(default_factory=list)


class ImportanceScorer:
    """
    重要度スコアラー.
    
    論文の重要度を多因子で評価。
    """

    def score(self, doc_id: str, title: str, abstract: str,
              year: Optional[int] = None,
              journal: Optional[str] = None,
              citations: int = 0) -> ScoringResult:
        """重要度をスコア."""
        factors = {}

        # 1. Novelty signals
        novelty_keywords = ["novel", "first", "new", "unique", "breakthrough"]
        novelty_score = sum(1 for kw in novelty_keywords if kw in abstract.lower())
        factors["novelty"] = min(novelty_score * 0.2, 1.0)

        # 2. Impact signals
        impact_keywords = ["significant", "major", "important", "clinical"]
        impact_score = sum(1 for kw in impact_keywords if kw in abstract.lower())
        factors["impact"] = min(impact_score * 0.15, 1.0)

        # 3. Recency (newer = higher)
        if year:
            current_year = 2024
            age = current_year - year
            factors["recency"] = max(0, 1 - age * 0.1)
        else:
            factors["recency"] = 0.5

        # 4. Journal quality (simplified)
        high_impact_journals = ["nature", "science", "cell", "lancet", "nejm"]
        if journal:
            journal_lower = journal.lower()
            factors["journal"] = 0.8 if any(j in journal_lower for j in high_impact_journals) else 0.5
        else:
            factors["journal"] = 0.5

        # 5. Citation impact
        factors["citations"] = min(citations / 100, 1.0)

        # Overall score
        weights = {"novelty": 0.25, "impact": 0.25, "recency": 0.2,
                   "journal": 0.15, "citations": 0.15}
        overall = sum(factors[k] * weights[k] for k in weights)

        explanation = f"重要度スコア: 新規性{factors['novelty']:.2f}, 影響度{factors['impact']:.2f}"

        return ScoringResult(
            score_name="importance",
            value=overall,
            explanation=explanation,
            factors=factors
        )


class ConfidenceScorer:
    """
    Claim信頼度スコアラー.
    
    主張の信頼度を評価。
    """

    def score(self, claim: Claim) -> ScoringResult:
        """Claimの信頼度をスコア."""
        factors = {}

        # 1. Evidence count
        evidence_count = len(claim.evidence)
        factors["evidence_count"] = min(evidence_count / 3, 1.0)

        # 2. Evidence quality
        if claim.evidence:
            avg_conf = sum(e.confidence for e in claim.evidence) / len(claim.evidence)
            factors["evidence_quality"] = avg_conf
        else:
            factors["evidence_quality"] = 0.0

        # 3. Hedging language (lower confidence if hedged)
        hedging = ["may", "might", "could", "possibly", "suggests", "appears"]
        claim_lower = claim.claim_text.lower()
        hedging_count = sum(1 for h in hedging if h in claim_lower)
        factors["certainty"] = max(0, 1 - hedging_count * 0.15)

        # 4. Quantitative support
        has_numbers = bool(re.search(r'\d+(?:\.\d+)?%?', claim.claim_text))
        factors["quantitative"] = 0.8 if has_numbers else 0.4

        # Overall
        weights = {"evidence_count": 0.3, "evidence_quality": 0.3,
                   "certainty": 0.2, "quantitative": 0.2}
        overall = sum(factors[k] * weights[k] for k in weights)

        explanation = f"根拠数{evidence_count}, 確実性{factors['certainty']:.2f}"

        return ScoringResult(
            score_name="confidence",
            value=overall,
            explanation=explanation,
            factors=factors,
            evidence=claim.evidence[:3]
        )


class BiasRiskScorer:
    """
    バイアスリスクスコアラー.
    
    研究のバイアスリスクを評価。
    """

    BIAS_INDICATORS = {
        "selection_bias": ["convenience sample", "non-random", "selected"],
        "performance_bias": ["not blinded", "open-label", "unblinded"],
        "detection_bias": ["subjective", "self-reported"],
        "attrition_bias": ["dropout", "lost to follow-up", "withdrawal"],
        "reporting_bias": ["post-hoc", "exploratory", "subgroup"],
        "conflict_interest": ["funded by", "received funding", "consultant"],
    }

    def score(self, text: str, doc_id: str = "") -> ScoringResult:
        """バイアスリスクをスコア."""
        factors = {}
        text_lower = text.lower()

        for bias_type, indicators in self.BIAS_INDICATORS.items():
            count = sum(1 for ind in indicators if ind in text_lower)
            factors[bias_type] = min(count * 0.3, 1.0)

        # Lower is better for bias
        overall_risk = sum(factors.values()) / len(factors)

        # Convert to "quality" score (high = low bias)
        quality_score = 1 - overall_risk

        high_risks = [k for k, v in factors.items() if v > 0.3]
        explanation = f"バイアスリスク: {', '.join(high_risks) if high_risks else 'Low'}"

        return ScoringResult(
            score_name="bias_risk",
            value=quality_score,
            explanation=explanation,
            factors=factors
        )


class EvidenceTierScorer:
    """
    エビデンス階層スコアラー.
    
    研究タイプに基づくエビデンスレベル。
    """

    TIERS = {
        "meta-analysis": 1.0,
        "systematic review": 0.95,
        "randomized controlled trial": 0.85,
        "rct": 0.85,
        "cohort study": 0.7,
        "case-control": 0.6,
        "cross-sectional": 0.5,
        "case report": 0.3,
        "case series": 0.35,
        "expert opinion": 0.2,
        "in vitro": 0.4,
        "in vivo": 0.5,
        "animal study": 0.45,
    }

    def score(self, text: str, doc_id: str = "") -> ScoringResult:
        """エビデンス階層をスコア."""
        text_lower = text.lower()

        detected_types = []
        highest_tier = 0.3  # Default

        for study_type, tier in self.TIERS.items():
            if study_type in text_lower:
                detected_types.append(study_type)
                if tier > highest_tier:
                    highest_tier = tier

        explanation = f"研究タイプ: {', '.join(detected_types) if detected_types else 'Unknown'}"

        return ScoringResult(
            score_name="evidence_tier",
            value=highest_tier,
            explanation=explanation,
            factors={t: self.TIERS[t] for t in detected_types}
        )


class LearningROIScorer:
    """
    Learning ROIスコアラー.
    
    学習効率（読む価値）を評価。
    """

    def score(self, doc_id: str, title: str, abstract: str,
              user_goal: str, user_domain: str) -> ScoringResult:
        """Learning ROIをスコア."""
        factors = {}

        # 1. Goal relevance
        goal_words = set(user_goal.lower().split())
        title_words = set(title.lower().split())
        abstract_words = set(abstract.lower().split())

        goal_overlap = len(goal_words & (title_words | abstract_words))
        factors["goal_relevance"] = min(goal_overlap / max(len(goal_words), 1), 1.0)

        # 2. Domain match
        if user_domain.lower() in abstract.lower():
            factors["domain_match"] = 0.9
        else:
            factors["domain_match"] = 0.4

        # 3. Readability (shorter = more accessible)
        word_count = len(abstract.split())
        factors["readability"] = max(0, 1 - word_count / 500)

        # 4. Actionability
        actionable_keywords = ["recommend", "should", "guidelines", "protocol",
                              "treatment", "intervention", "strategy"]
        actionable_count = sum(1 for kw in actionable_keywords if kw in abstract.lower())
        factors["actionability"] = min(actionable_count * 0.2, 1.0)

        # Overall
        weights = {"goal_relevance": 0.4, "domain_match": 0.25,
                   "readability": 0.15, "actionability": 0.2}
        overall = sum(factors[k] * weights[k] for k in weights)

        explanation = f"目標適合度{factors['goal_relevance']:.2f}, ドメイン一致{factors['domain_match']:.2f}"

        return ScoringResult(
            score_name="learning_roi",
            value=overall,
            explanation=explanation,
            factors=factors
        )


class ScoringPlugin:
    """Scoring統合プラグイン."""

    def __init__(self):
        self.importance = ImportanceScorer()
        self.confidence = ConfidenceScorer()
        self.bias = BiasRiskScorer()
        self.evidence_tier = EvidenceTierScorer()
        self.learning_roi = LearningROIScorer()
        self.is_active = False

    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        self.is_active = True

    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """スコアリングを実行."""
        delta: ArtifactsDelta = {
            "paper_scores": {},
            "claim_scores": {}
        }

        for paper in artifacts.papers:
            paper_text = paper.abstract or ""

            # Paper-level scores
            importance = self.importance.score(
                paper.doc_id, paper.title, paper_text,
                paper.year, paper.journal
            )
            bias = self.bias.score(paper_text, paper.doc_id)
            tier = self.evidence_tier.score(paper_text, paper.doc_id)
            roi = self.learning_roi.score(
                paper.doc_id, paper.title, paper_text,
                context.goal, context.domain
            )

            delta["paper_scores"][paper.doc_id] = {
                "importance": {
                    "value": importance.value,
                    "explanation": importance.explanation,
                    "factors": importance.factors
                },
                "bias_risk": {
                    "value": bias.value,
                    "explanation": bias.explanation,
                    "factors": bias.factors
                },
                "evidence_tier": {
                    "value": tier.value,
                    "explanation": tier.explanation
                },
                "learning_roi": {
                    "value": roi.value,
                    "explanation": roi.explanation,
                    "factors": roi.factors
                }
            }

            # Store in artifacts
            artifacts.scores[f"{paper.doc_id}_importance"] = Score(
                name="importance", value=importance.value,
                explanation=importance.explanation
            )
            artifacts.scores[f"{paper.doc_id}_roi"] = Score(
                name="learning_roi", value=roi.value,
                explanation=roi.explanation
            )

        # Claim-level scores
        for claim in artifacts.claims:
            conf = self.confidence.score(claim)
            delta["claim_scores"][claim.claim_id] = {
                "confidence": {
                    "value": conf.value,
                    "explanation": conf.explanation,
                    "factors": conf.factors
                }
            }

        return delta

    def deactivate(self) -> None:
        self.is_active = False


def get_scoring_plugin() -> ScoringPlugin:
    return ScoringPlugin()
