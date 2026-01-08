"""JARVIS Evidence Grading Module.

Evidence grading and classification for systematic reviews.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.1

This module provides:
- Evidence level classification (CEBM Oxford scale)
- Study type detection (RCT, cohort, case-control, etc.)
- Rule-based and LLM-based classifiers
- Ensemble grading with confidence scores
"""

from jarvis_core.evidence.schema import (
    EvidenceLevel,
    EvidenceGrade,
    StudyType,
)
from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
from jarvis_core.evidence.llm_classifier import LLMBasedClassifier
from jarvis_core.evidence.ensemble import EnsembleClassifier, grade_evidence

# English descriptions for evidence levels (CEBM Oxford 2011)
EVIDENCE_LEVEL_DESCRIPTIONS_EN = {
    "1a": "Systematic review of homogeneous RCTs",
    "1b": "Individual RCT with narrow confidence interval",
    "1c": "All or none study",
    "2a": "Systematic review of homogeneous cohort studies",
    "2b": "Individual cohort study (including low-quality RCT)",
    "2c": "Outcomes research; ecological studies",
    "3a": "Systematic review of homogeneous case-control studies",
    "3b": "Individual case-control study",
    "4": "Case series (and poor quality cohort and case-control studies)",
    "5": "Expert opinion without explicit critical appraisal",
    "unknown": "Unknown or unclassified",
}

__all__ = [
    "EvidenceLevel",
    "EvidenceGrade",
    "StudyType",
    "RuleBasedClassifier",
    "LLMBasedClassifier",
    "EnsembleClassifier",
    "grade_evidence",
    "EVIDENCE_LEVEL_DESCRIPTIONS_EN",
]
