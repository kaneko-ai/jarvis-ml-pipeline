"""Tests for evidence grading module."""
import pytest
from jarvis_core.evidence import grade_evidence


class TestEvidenceGrading:
    def test_grade_rct(self):
        paper = {
            "title": "A randomized controlled trial of PD-1 blockade",
            "abstract": "This randomized controlled trial investigated...",
        }
        result = grade_evidence(paper)
        assert result is not None
        assert hasattr(result, "level")
        assert hasattr(result, "study_type")

    def test_grade_review(self):
        paper = {
            "title": "Systematic review of autophagy in aging",
            "abstract": "This systematic review and meta-analysis...",
        }
        result = grade_evidence(paper)
        assert result is not None
        assert hasattr(result, "level")

    def test_grade_empty(self):
        paper = {"title": "", "abstract": ""}
        result = grade_evidence(paper)
        assert result is not None
        assert hasattr(result, "level")

    def test_to_dict(self):
        paper = {
            "title": "A cohort study of spermidine",
            "abstract": "This cohort study examined...",
        }
        result = grade_evidence(paper)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "level" in d
