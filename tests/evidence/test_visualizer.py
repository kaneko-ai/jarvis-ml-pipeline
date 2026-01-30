"""Tests for Evidence Visualizer."""

from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
from jarvis_core.evidence.visualizer import EvidenceVisualizer


def test_generate_confidence_chart():
    visualizer = EvidenceVisualizer()

    grades = [
        EvidenceGrade(
            level=EvidenceLevel.LEVEL_1A, confidence=0.9, study_type=StudyType.META_ANALYSIS
        ),
        EvidenceGrade(
            level=EvidenceLevel.LEVEL_1A, confidence=0.85, study_type=StudyType.META_ANALYSIS
        ),
        EvidenceGrade(
            level=EvidenceLevel.LEVEL_2B, confidence=0.7, study_type=StudyType.COHORT_PROSPECTIVE
        ),
        EvidenceGrade(
            level=EvidenceLevel.LEVEL_3B, confidence=0.6, study_type=StudyType.CASE_CONTROL
        ),
    ]

    chart = visualizer.generate_confidence_chart(grades)

    assert "pie title Evidence Level Distribution" in chart
    assert "1a" in chart.lower() or "level_1a" in chart.lower()


def test_generate_summary_table():
    visualizer = EvidenceVisualizer()

    grades = [
        EvidenceGrade(
            level=EvidenceLevel.LEVEL_1A,
            confidence=0.9,
            study_type=StudyType.META_ANALYSIS,
            classifier_source="ensemble",
        ),
    ]

    table = visualizer.generate_summary_table(grades)

    assert "|" in table
    assert "Level" in table
    assert "Confidence" in table
