"""Comprehensive functional tests for stages module.

These tests go beyond import checks to test actual pipeline stage functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import uuid


# ============================================================
# Tests for stages/extract_claims.py (23% coverage)
# ============================================================

class TestExtractClaimsFunction:
    """Tests for extract_claims function."""

    def test_extract_claims_empty_papers(self):
        from jarvis_core.stages.extract_claims import extract_claims
        result = extract_claims([])
        assert result["claims"] == []
        assert result["count"] == 0
        assert result["stage"] == "extraction.claims"

    def test_extract_claims_single_paper(self):
        from jarvis_core.stages.extract_claims import extract_claims
        papers = [
            {
                "paper_id": "paper_001",
                "title": "Machine Learning in Healthcare",
                "abstract": "This study investigates the application of machine learning algorithms to healthcare diagnostics. We found significant improvements in accuracy."
            }
        ]
        result = extract_claims(papers)
        assert result["count"] > 0
        assert len(result["claims"]) > 0
        assert all("claim_id" in c for c in result["claims"])
        assert all("claim_text" in c for c in result["claims"])

    def test_extract_claims_multiple_papers(self):
        from jarvis_core.stages.extract_claims import extract_claims
        papers = [
            {"paper_id": f"paper_{i}", "title": f"Paper {i} Title", "abstract": f"Abstract for paper {i} with sufficient content to extract claims."}
            for i in range(10)
        ]
        result = extract_claims(papers)
        assert result["count"] > 0
        assert result["source_papers"] == 10

    def test_extract_claims_with_kwargs(self):
        from jarvis_core.stages.extract_claims import extract_claims
        papers = [{"paper_id": "p1", "title": "Test", "abstract": "Test abstract with enough text."}]
        result = extract_claims(papers, task_id="task_123")
        assert isinstance(result, dict)

    def test_claim_structure(self):
        from jarvis_core.stages.extract_claims import extract_claims
        papers = [{"paper_id": "test_paper", "title": "Test Title", "abstract": "A sufficiently long abstract for testing claim extraction."}]
        result = extract_claims(papers)
        if result["claims"]:
            claim = result["claims"][0]
            assert "claim_id" in claim
            assert "claim_text" in claim
            assert "claim_type" in claim
            assert "source_paper_id" in claim


# ============================================================
# Tests for stages/find_evidence.py (26% coverage)
# ============================================================

class TestFindEvidenceFunction:
    """Tests for find_evidence function."""

    def test_find_evidence_empty_claims(self):
        from jarvis_core.stages.find_evidence import find_evidence
        result = find_evidence([], {})
        assert result["evidence"] == []
        assert result["count"] == 0

    def test_find_evidence_no_matching_papers(self):
        from jarvis_core.stages.find_evidence import find_evidence
        claims = [
            {"claim_id": "c1", "claim_text": "Test claim", "source_paper_id": "nonexistent"}
        ]
        papers = {}
        result = find_evidence(claims, papers)
        assert result["count"] == 0

    def test_find_evidence_with_matching_paper(self):
        from jarvis_core.stages.find_evidence import find_evidence
        claims = [
            {"claim_id": "c1", "claim_text": "Test claim text", "source_paper_id": "paper_1"}
        ]
        papers = {
            "paper_1": {"paper_id": "paper_1", "title": "Test Paper", "abstract": "Test abstract"}
        }
        result = find_evidence(claims, papers)
        assert result["count"] > 0
        assert len(result["evidence"]) > 0

    def test_evidence_structure(self):
        from jarvis_core.stages.find_evidence import find_evidence
        claims = [{"claim_id": "claim_test", "claim_text": "Test claim", "source_paper_id": "p1"}]
        papers = {"p1": {"paper_id": "p1"}}
        result = find_evidence(claims, papers)
        if result["evidence"]:
            ev = result["evidence"][0]
            assert "evidence_id" in ev
            assert "claim_id" in ev
            assert "paper_id" in ev
            assert "locator" in ev


# ============================================================
# Tests for stages/grade_evidence.py (10% coverage)
# ============================================================

class TestCalculateEvidenceStrength:
    """Tests for calculate_evidence_strength function."""

    def test_strong_evidence(self):
        from jarvis_core.stages.grade_evidence import calculate_evidence_strength
        evidence = {
            "paper_id": "p1",
            "quote_span": "A" * 150,
            "evidence_role": "Direct"
        }
        claim = {"source_paper_id": "p1"}
        strength = calculate_evidence_strength(evidence, claim)
        assert strength == "Strong"

    def test_medium_evidence(self):
        from jarvis_core.stages.grade_evidence import calculate_evidence_strength
        evidence = {
            "paper_id": "p2",
            "quote_span": "A" * 80,
            "evidence_role": "Direct"
        }
        claim = {"source_paper_id": "p1"}
        strength = calculate_evidence_strength(evidence, claim)
        assert strength == "Medium"

    def test_weak_evidence(self):
        from jarvis_core.stages.grade_evidence import calculate_evidence_strength
        evidence = {
            "paper_id": "p2",
            "quote_span": "A" * 30,
            "evidence_role": "Other"
        }
        claim = {"source_paper_id": "p1"}
        strength = calculate_evidence_strength(evidence, claim)
        assert strength == "Weak"

    def test_no_evidence(self):
        from jarvis_core.stages.grade_evidence import calculate_evidence_strength
        evidence = {
            "paper_id": "p2",
            "quote_span": "Short",
            "evidence_role": "Other"
        }
        claim = {"source_paper_id": "p1"}
        strength = calculate_evidence_strength(evidence, claim)
        assert strength == "None"


class TestGradeEvidenceFunction:
    """Tests for grade_evidence function."""

    def test_grade_evidence_empty(self):
        from jarvis_core.stages.grade_evidence import grade_evidence
        result = grade_evidence([], [])
        assert result["support_rate"] == 0.0
        assert result["unsupported_count"] == 0

    def test_grade_evidence_all_supported(self):
        from jarvis_core.stages.grade_evidence import grade_evidence
        claims = [
            {"claim_id": "c1", "source_paper_id": "p1"},
            {"claim_id": "c2", "source_paper_id": "p1"},
        ]
        evidence = [
            {"claim_id": "c1", "paper_id": "p1", "quote_span": "A" * 200, "evidence_role": "Direct"},
            {"claim_id": "c2", "paper_id": "p1", "quote_span": "B" * 150, "evidence_role": "Direct"},
        ]
        result = grade_evidence(claims, evidence)
        assert result["support_rate"] == 1.0
        assert result["unsupported_count"] == 0

    def test_grade_evidence_some_unsupported(self):
        from jarvis_core.stages.grade_evidence import grade_evidence
        claims = [
            {"claim_id": "c1", "source_paper_id": "p1"},
            {"claim_id": "c2", "source_paper_id": "p1"},
        ]
        evidence = [
            {"claim_id": "c1", "paper_id": "p1", "quote_span": "A" * 200, "evidence_role": "Direct"},
        ]
        result = grade_evidence(claims, evidence)
        assert result["support_rate"] == 0.5
        assert result["unsupported_count"] == 1


# ============================================================
# Tests for stages/generate_report.py
# ============================================================

class TestGenerateReport:
    """Tests for report generation stage."""

    def test_import_generate_report(self):
        from jarvis_core.stages import generate_report
        assert hasattr(generate_report, "__name__")


# ============================================================
# Tests for stages/find_counter_evidence.py
# ============================================================

class TestFindCounterEvidence:
    """Tests for counter-evidence finding stage."""

    def test_import_find_counter_evidence(self):
        from jarvis_core.stages import find_counter_evidence
        assert hasattr(find_counter_evidence, "__name__")


# ============================================================
# Tests for stages/output_quality.py
# ============================================================

class TestOutputQuality:
    """Tests for output quality stage."""

    def test_import_output_quality(self):
        from jarvis_core.stages import output_quality
        assert hasattr(output_quality, "__name__")


# ============================================================
# Tests for stages/summarization_scoring.py
# ============================================================

class TestSummarizationScoring:
    """Tests for summarization scoring stage."""

    def test_import_summarization_scoring(self):
        from jarvis_core.stages import summarization_scoring
        assert hasattr(summarization_scoring, "__name__")


# ============================================================
# Tests for stages/retrieval_extraction.py
# ============================================================

class TestRetrievalExtraction:
    """Tests for retrieval extraction stage."""

    def test_import_retrieval_extraction(self):
        from jarvis_core.stages import retrieval_extraction
        assert hasattr(retrieval_extraction, "__name__")


# ============================================================
# Tests for stages/extract_features.py
# ============================================================

class TestExtractFeatures:
    """Tests for feature extraction stage."""

    def test_import_extract_features(self):
        from jarvis_core.stages import extract_features
        assert hasattr(extract_features, "__name__")
