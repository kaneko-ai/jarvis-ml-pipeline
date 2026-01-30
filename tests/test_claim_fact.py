"""Tests for truth_validation.claim_fact module."""

from unittest.mock import MagicMock

from jarvis_core.truth_validation.claim_fact import (
    AlignmentResult,
    ClaimFactChecker,
    check_claim_fact_alignment,
    enforce_evidence_ref,
)


class TestAlignmentResult:
    def test_creation(self):
        result = AlignmentResult(
            claim_text="Test claim",
            status="aligned",
            evidence_coverage=0.85,
            matched_facts=["Fact 1"],
            issues=[],
        )
        assert result.status == "aligned"
        assert result.evidence_coverage == 0.85

    def test_to_dict(self):
        result = AlignmentResult(
            claim_text="A very long claim text that exceeds the truncation limit",
            status="partial",
            evidence_coverage=0.5,
            matched_facts=["Fact"],
            issues=["Issue 1"],
        )
        d = result.to_dict()

        assert "claim_text" in d
        assert "status" in d
        assert "evidence_coverage" in d


class TestClaimFactChecker:
    def test_tokenize(self):
        tokens = ClaimFactChecker.tokenize("The quick brown fox jumps")

        assert "quick" in tokens
        assert "brown" in tokens
        assert "fox" in tokens
        # Stopwords removed
        assert "the" not in tokens

    def test_tokenize_removes_short_words(self):
        tokens = ClaimFactChecker.tokenize("a to in on for")
        assert len(tokens) == 0

    def test_calculate_overlap_full(self):
        overlap = ClaimFactChecker.calculate_overlap(
            "machine learning models",
            "machine learning models are useful",
        )
        assert overlap > 0.8

    def test_calculate_overlap_partial(self):
        overlap = ClaimFactChecker.calculate_overlap(
            "machine learning",
            "deep learning networks",
        )
        assert 0 < overlap < 0.8

    def test_calculate_overlap_none(self):
        overlap = ClaimFactChecker.calculate_overlap(
            "cats dogs",
            "mathematics physics",
        )
        assert overlap == 0.0

    def test_check_alignment_no_facts(self):
        checker = ClaimFactChecker()
        result = checker.check_alignment("Some claim", facts=[])

        assert result.status == "misaligned"
        assert result.evidence_coverage == 0.0
        assert len(result.issues) > 0

    def test_check_alignment_with_matching_fact(self):
        checker = ClaimFactChecker()

        # Create mock fact
        mock_fact = MagicMock()
        mock_fact.statement = "Machine learning models can predict outcomes"
        mock_fact.evidence_refs = []

        result = checker.check_alignment(
            "Machine learning models predict outcomes accurately",
            facts=[mock_fact],
        )

        assert result.status in ["aligned", "partial"]
        assert result.evidence_coverage > 0


class TestCheckClaimFactAlignment:
    def test_check_multiple_claims(self):
        mock_fact = MagicMock()
        mock_fact.statement = "Test evidence statement"
        mock_fact.evidence_refs = []

        claims = ["Claim one", "Claim two"]
        results = check_claim_fact_alignment(claims, [mock_fact])

        assert len(results) == 2
        assert all(isinstance(r, AlignmentResult) for r in results)


class TestEnforceEvidenceRef:
    def test_with_evidence(self):
        level, stmt = enforce_evidence_ref("Statement with evidence", has_evidence=True)

        assert level == "fact"
        assert stmt == "Statement with evidence"

    def test_without_evidence(self):
        level, stmt = enforce_evidence_ref("Statement without evidence", has_evidence=False)

        assert level == "inference"
        assert "推定" in stmt