"""Tests for truth.alignment module."""

from unittest.mock import MagicMock

from jarvis_core.truth.alignment import (
    AlignmentResult,
    tokenize,
    calculate_token_overlap,
    check_locator_match,
    check_alignment_v2,
)


class TestAlignmentResult:
    def test_to_dict(self):
        result = AlignmentResult(
            claim="Test claim about cancer treatment",
            status="aligned",
            score=0.75,
            token_overlap=0.8,
            locator_match=True,
            mismatch_reasons=[],
            matched_fact="Supporting fact",
        )
        d = result.to_dict()
        
        assert d["status"] == "aligned"
        assert d["score"] == 0.75
        assert d["token_overlap"] == 0.8
        assert d["locator_match"] is True


class TestTokenize:
    def test_tokenize_removes_stopwords(self):
        tokens = tokenize("The drug is effective for the treatment")
        
        assert "the" not in tokens
        assert "is" not in tokens
        assert "drug" in tokens
        assert "effective" in tokens

    def test_tokenize_removes_short_words(self):
        tokens = tokenize("A big cat is on the mat")
        
        assert "a" not in tokens
        assert "is" not in tokens
        assert "on" not in tokens


class TestCalculateTokenOverlap:
    def test_full_overlap(self):
        overlap = calculate_token_overlap(
            "drug treatment effective",
            "drug treatment effective"
        )
        assert overlap == 1.0

    def test_partial_overlap(self):
        overlap = calculate_token_overlap(
            "drug treatment therapy",
            "drug therapy medicine"
        )
        assert 0 < overlap < 1

    def test_no_overlap(self):
        overlap = calculate_token_overlap(
            "apple banana cherry",
            "house car bicycle"
        )
        assert overlap == 0.0

    def test_empty_text(self):
        overlap = calculate_token_overlap("", "some text")
        assert overlap == 0.0


class TestCheckLocatorMatch:
    def test_matching_locator(self):
        result = check_locator_match("page:5", ["page:5", "page:6"])
        assert result is True

    def test_partial_match(self):
        result = check_locator_match("page", ["page:5:para:2"])
        assert result is True

    def test_no_match(self):
        result = check_locator_match("page:10", ["page:5", "page:6"])
        assert result is False

    def test_empty_locators(self):
        result = check_locator_match("page:5", [])
        assert result is False

    def test_empty_claim_locator(self):
        result = check_locator_match("", ["page:5"])
        assert result is False


class TestCheckAlignmentV2:
    def test_aligned_with_facts(self):
        claim = "Drug effectively treats cancer cells"
        
        fact = MagicMock()
        fact.statement = "Drug effectively treats cancer cells"
        fact.evidence_refs = []
        
        result = check_alignment_v2(claim, [fact])
        
        assert result.status == "aligned"
        assert result.score > 0.6

    def test_misaligned_no_facts(self):
        result = check_alignment_v2("Some claim", [])
        
        assert result.status == "misaligned"
        assert result.score == 0.0
        assert "No supporting facts" in result.mismatch_reasons[0]

    def test_partial_alignment(self):
        claim = "Drug A treats cancer"
        
        fact = MagicMock()
        fact.statement = "Drug B treats tumors and cancer cells"
        fact.evidence_refs = []
        
        result = check_alignment_v2(claim, [fact])
        
        # Should be partial due to some token overlap
        assert result.token_overlap > 0

    def test_alignment_with_evidence_snippet(self):
        claim = "Treatment is effective"
        
        fact = MagicMock()
        fact.statement = "Different statement about therapy"
        
        evidence_ref = MagicMock()
        evidence_ref.text_snippet = "Treatment is effective for patients"
        evidence_ref.source_locator = "page:5"
        fact.evidence_refs = [evidence_ref]
        
        result = check_alignment_v2(claim, [fact], claim_locator="page:5")
        
        assert result.token_overlap > 0
        assert result.locator_match is True
