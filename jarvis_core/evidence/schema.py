"""Evidence Grading Schema.

Defines evidence levels and study types for systematic reviews.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.1 Schema
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from jarvis_core.evidence.uncertainty import determine_uncertainty_label


class EvidenceLevel(Enum):
    """Oxford Centre for Evidence-Based Medicine (CEBM) Evidence Levels.

    Level 1: Systematic reviews / RCTs
    Level 2: Cohort studies
    Level 3: Case-control studies
    Level 4: Case series
    Level 5: Expert opinion
    """

    LEVEL_1A = "1a"  # 系統的レビュー（均質なRCT）
    LEVEL_1B = "1b"  # 個別のRCT（狭い信頼区間）
    LEVEL_1C = "1c"  # 全か無かの研究

    LEVEL_2A = "2a"  # 系統的レビュー（均質なコホート研究）
    LEVEL_2B = "2b"  # 個別のコホート研究
    LEVEL_2C = "2c"  # 結果研究・生態学的研究

    LEVEL_3A = "3a"  # 系統的レビュー（均質な症例対照研究）
    LEVEL_3B = "3b"  # 個別の症例対照研究

    LEVEL_4 = "4"  # 症例シリーズ

    LEVEL_5 = "5"  # 専門家意見

    UNKNOWN = "unknown"

    @property
    def numeric_rank(self) -> int:
        """Get numeric rank (1=highest, 5=lowest)."""
        rank_map = {
            "1a": 1,
            "1b": 2,
            "1c": 3,
            "2a": 4,
            "2b": 5,
            "2c": 6,
            "3a": 7,
            "3b": 8,
            "4": 9,
            "5": 10,
            "unknown": 11,
        }
        return rank_map.get(self.value, 11)

    @property
    def description(self) -> str:
        """Get human-readable description."""
        descriptions = {
            "1a": "系統的レビュー（均質なRCT）",
            "1b": "個別のRCT（狭い信頼区間）",
            "1c": "全か無かの研究",
            "2a": "系統的レビュー（均質なコホート研究）",
            "2b": "個別のコホート研究",
            "2c": "結果研究・生態学的研究",
            "3a": "系統的レビュー（均質な症例対照研究）",
            "3b": "個別の症例対照研究",
            "4": "症例シリーズ",
            "5": "専門家意見",
            "unknown": "不明",
        }
        return descriptions.get(self.value, "不明")

    def __lt__(self, other: EvidenceLevel) -> bool:
        return self.numeric_rank < other.numeric_rank


class StudyType(Enum):
    """Types of research studies."""

    # Systematic reviews and meta-analyses
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"

    # Experimental studies
    RCT = "randomized_controlled_trial"
    CLUSTER_RCT = "cluster_randomized_trial"
    CROSSOVER_TRIAL = "crossover_trial"
    NON_RANDOMIZED_TRIAL = "non_randomized_trial"

    # Observational studies
    COHORT_PROSPECTIVE = "prospective_cohort"
    COHORT_RETROSPECTIVE = "retrospective_cohort"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    CASE_SERIES = "case_series"
    CASE_REPORT = "case_report"

    # Other
    NARRATIVE_REVIEW = "narrative_review"
    EXPERT_OPINION = "expert_opinion"
    GUIDELINE = "clinical_guideline"
    UNKNOWN = "unknown"

    @property
    def default_evidence_level(self) -> EvidenceLevel:
        """Get default evidence level for this study type."""
        mapping = {
            StudyType.SYSTEMATIC_REVIEW: EvidenceLevel.LEVEL_1A,
            StudyType.META_ANALYSIS: EvidenceLevel.LEVEL_1A,
            StudyType.RCT: EvidenceLevel.LEVEL_1B,
            StudyType.CLUSTER_RCT: EvidenceLevel.LEVEL_1B,
            StudyType.CROSSOVER_TRIAL: EvidenceLevel.LEVEL_1B,
            StudyType.NON_RANDOMIZED_TRIAL: EvidenceLevel.LEVEL_2B,
            StudyType.COHORT_PROSPECTIVE: EvidenceLevel.LEVEL_2B,
            StudyType.COHORT_RETROSPECTIVE: EvidenceLevel.LEVEL_2B,
            StudyType.CASE_CONTROL: EvidenceLevel.LEVEL_3B,
            StudyType.CROSS_SECTIONAL: EvidenceLevel.LEVEL_4,
            StudyType.CASE_SERIES: EvidenceLevel.LEVEL_4,
            StudyType.CASE_REPORT: EvidenceLevel.LEVEL_4,
            StudyType.NARRATIVE_REVIEW: EvidenceLevel.LEVEL_5,
            StudyType.EXPERT_OPINION: EvidenceLevel.LEVEL_5,
            StudyType.GUIDELINE: EvidenceLevel.LEVEL_5,
            StudyType.UNKNOWN: EvidenceLevel.UNKNOWN,
        }
        return mapping.get(self, EvidenceLevel.UNKNOWN)


@dataclass
class EvidenceGrade:
    """Complete evidence grading result."""

    level: EvidenceLevel
    study_type: StudyType
    confidence: float  # 0.0 to 1.0
    uncertainty_label: str | None = None

    # Optional details
    sample_size: int | None = None
    population: str | None = None
    intervention: str | None = None
    comparator: str | None = None
    outcome: str | None = None

    # Quality assessment
    risk_of_bias: str | None = None  # "low", "moderate", "high"
    quality_notes: list[str] = field(default_factory=list)

    # Classification source
    classifier_source: str = "unknown"  # "rule", "llm", "ensemble"
    raw_scores: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.uncertainty_label is None:
            self.uncertainty_label = determine_uncertainty_label(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "level_description": self.level.description,
            "study_type": self.study_type.value,
            "confidence": self.confidence,
            "uncertainty_label": self.uncertainty_label,
            "sample_size": self.sample_size,
            "population": self.population,
            "intervention": self.intervention,
            "comparator": self.comparator,
            "outcome": self.outcome,
            "risk_of_bias": self.risk_of_bias,
            "quality_notes": self.quality_notes,
            "classifier_source": self.classifier_source,
            "raw_scores": self.raw_scores,
        }

    @classmethod
    def unknown(cls) -> EvidenceGrade:
        """Create an unknown grade."""
        return cls(
            level=EvidenceLevel.UNKNOWN,
            study_type=StudyType.UNKNOWN,
            confidence=0.0,
            classifier_source="unknown",
        )


# PICO components for evidence extraction
@dataclass
class PICOExtraction:
    """PICO (Population, Intervention, Comparator, Outcome) extraction."""

    population: str | None = None
    intervention: str | None = None
    comparator: str | None = None
    outcome: str | None = None

    # Additional details
    study_duration: str | None = None
    setting: str | None = None

    def is_complete(self) -> bool:
        """Check if all PICO components are present."""
        return all(
            [
                self.population,
                self.intervention,
                self.comparator,
                self.outcome,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "population": self.population,
            "intervention": self.intervention,
            "comparator": self.comparator,
            "outcome": self.outcome,
            "study_duration": self.study_duration,
            "setting": self.setting,
        }
