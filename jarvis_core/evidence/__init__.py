"""JARVIS Evidence Grading Module.

Evidence grading and classification for systematic reviews.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.1
"""

from jarvis_core.evidence.schema import (
    EvidenceLevel,
    EvidenceGrade,
    StudyType,
)
from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
from jarvis_core.evidence.llm_classifier import LLMBasedClassifier
from jarvis_core.evidence.ensemble import EnsembleClassifier, grade_evidence

__all__ = [
    "EvidenceLevel",
    "EvidenceGrade",
    "StudyType",
    "RuleBasedClassifier",
    "LLMBasedClassifier",
    "EnsembleClassifier",
    "grade_evidence",
]
