"""Tests for Report Generation with Evidence IDs (Phase 2)."""

from jarvis_core.reporting.report_schema import Conclusion, validate_conclusion
from jarvis_core.reporting.uncertainty import determine_uncertainty
from jarvis_core.stages.generate_report import (
    build_evidence_map,
    determine_support_level,
)


class TestUncertaintyDetermination:
    """Test uncertainty label determination."""

    def test_strong_no_contradiction(self):
        assert determine_uncertainty("Strong", False) == "確定"

    def test_strong_with_contradiction(self):
        assert determine_uncertainty("Strong", True) == "高信頼"

    def test_medium_no_contradiction(self):
        assert determine_uncertainty("Medium", False) == "高信頼"

    def test_medium_with_contradiction(self):
        assert determine_uncertainty("Medium", True) == "要注意"

    def test_weak_support(self):
        assert determine_uncertainty("Weak", False) == "要注意"

    def test_none_support(self):
        assert determine_uncertainty("None", False) == "推測"


class TestSupportLevelDetermination:
    """Test support level determination from evidence."""

    def test_no_evidence(self):
        assert determine_support_level([]) == "None"

    def test_strong_evidence(self):
        evidence = [{"evidence_strength": "Strong"}]
        assert determine_support_level(evidence) == "Strong"

    def test_two_medium(self):
        evidence = [{"evidence_strength": "Medium"}, {"evidence_strength": "Medium"}]
        assert determine_support_level(evidence) == "Medium"

    def test_medium_and_weak(self):
        evidence = [{"evidence_strength": "Medium"}, {"evidence_strength": "Weak"}]
        assert determine_support_level(evidence) == "Medium"

    def test_only_weak(self):
        evidence = [{"evidence_strength": "Weak"}]
        assert determine_support_level(evidence) == "Weak"


class TestConclusionValidation:
    """Test conclusion validation rules."""

    def test_valid_strong_conclusion(self):
        conclusion = Conclusion(
            conclusion_text="CD73 is highly expressed",
            claim_id="claim_001",
            evidence_ids=["ev_001", "ev_002"],
            support_level="Strong",
            uncertainty_label="確定",
        )
        errors = validate_conclusion(conclusion)
        assert len(errors) == 0

    def test_strong_without_evidence_ids(self):
        conclusion = Conclusion(
            conclusion_text="CD73 is highly expressed",
            claim_id="claim_001",
            evidence_ids=[],
            support_level="Strong",
            uncertainty_label="確定",
        )
        errors = validate_conclusion(conclusion)
        assert len(errors) > 0
        assert "without evidence IDs" in errors[0]

    def test_none_support_with_assertive_language(self):
        conclusion = Conclusion(
            conclusion_text="CD73である",  # Assertive
            claim_id="claim_001",
            evidence_ids=[],
            support_level="None",
            uncertainty_label="推測",
        )
        errors = validate_conclusion(conclusion)
        assert len(errors) > 0
        assert "Assertive language" in errors[0]

    def test_uncertainty_mismatch(self):
        conclusion = Conclusion(
            conclusion_text="CD73 expression",
            claim_id="claim_001",
            evidence_ids=["ev_001"],
            support_level="Strong",
            uncertainty_label="推測",  # Should be 確定
        )
        errors = validate_conclusion(conclusion)
        assert len(errors) > 0
        assert "Uncertainty mismatch" in errors[0]


class TestEvidenceMapping:
    """Test evidence mapping logic."""

    def test_build_evidence_map(self):
        claims = [
            {"claim_id": "claim_001"},
            {"claim_id": "claim_002"},
        ]

        evidence = [
            {"evidence_id": "ev_001", "claim_id": "claim_001"},
            {"evidence_id": "ev_002", "claim_id": "claim_001"},
            {"evidence_id": "ev_003", "claim_id": "claim_002"},
        ]

        evidence_map = build_evidence_map(claims, evidence)

        assert len(evidence_map["claim_001"]) == 2
        assert len(evidence_map["claim_002"]) == 1