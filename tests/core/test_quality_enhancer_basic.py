import pytest
from jarvis_core.eval.quality_enhancer import (
    ClaimQualityEnhancer,
    EvidenceQualityEnhancer,
    enhance_claims,
    enhance_evidence,
    QualityScore,
)


@pytest.fixture
def claim_enhancer():
    return ClaimQualityEnhancer(min_quality=0.4)


@pytest.fixture
def evidence_enhancer():
    return EvidenceQualityEnhancer(min_quality=0.4)


class TestClaimQualityEnhancer:
    def test_enhance_basic(self, claim_enhancer):
        claims = [
            {"claim_text": "TP53 mutation is high in cancer patients."},
            {"claim_text": "This is a generic claim."},
        ]
        enhanced = claim_enhancer.enhance(claims)
        # Higher score first. TP53 one has specific numbers/names potentially.
        assert len(enhanced) >= 1
        assert "quality_score" in enhanced[0]
        assert "overall" in enhanced[0]["quality_score"]

    def test_deduplication(self, claim_enhancer):
        claims = [
            {"claim_text": "Duplicate claim text."},
            {"claim_text": "Duplicate claim text."},
        ]
        # min_quality=0.1 to ensure they stay
        enhancer = ClaimQualityEnhancer(min_quality=0.1)
        enhanced = enhancer.enhance(claims)
        assert len(enhanced) == 1

    def test_low_quality_filtering(self, claim_enhancer):
        claims = [{"claim_text": "Short."}]  # Very low quality
        enhancer = ClaimQualityEnhancer(min_quality=0.8)
        enhanced = enhancer.enhance(claims)
        assert len(enhanced) == 0

    def test_specificity_scoring(self, claim_enhancer):
        # Specific names and numbers
        text = "EGFR expression increased by 50% in the presence of 10μM compound X."
        score = claim_enhancer._calculate_specificity(text)
        assert score > 0.7

    def test_verifiability_scoring(self, claim_enhancer):
        text = "Results showed significant improvement (p<0.05)."
        score = claim_enhancer._calculate_verifiability(text)
        assert score > 0.7

        text_vague = "This may be true."
        score_vague = claim_enhancer._calculate_verifiability(text_vague)
        assert score_vague < score

    def test_uniqueness_scoring(self, claim_enhancer):
        text_generic = "This protein plays a role in some disease."
        score_generic = claim_enhancer._calculate_uniqueness(text_generic)
        assert score_generic < 0.7

    def test_completeness_scoring(self, claim_enhancer):
        text_bad = "bad"
        score_bad = claim_enhancer._calculate_completeness(text_bad)

        text_good = "The study was conducted according to the guidelines."
        score_good = claim_enhancer._calculate_completeness(text_good)
        assert score_good > score_bad


class TestEvidenceQualityEnhancer:
    def test_enhance_basic(self, evidence_enhancer):
        evidence = [
            {
                "evidence_text": "Significant increase observed in the treatment group.",
                "locator": {"section": "Results", "paragraph": 2},
            },
            {"evidence_text": "No locator here."},
        ]
        enhanced = evidence_enhancer.enhance(evidence)
        assert len(enhanced) >= 1
        assert "quality_score" in enhanced[0]

    def test_quality_with_locator(self, evidence_enhancer):
        ev_full = {"evidence_text": "Text", "locator": {"section": "S1", "paragraph": 1}}
        score_full = evidence_enhancer._calculate_quality(ev_full)

        ev_partial = {"evidence_text": "Text", "locator": {"section": "S1"}}
        score_partial = evidence_enhancer._calculate_quality(ev_partial)

        ev_none = {"evidence_text": "Text"}
        score_none = evidence_enhancer._calculate_quality(ev_none)

        assert score_full.completeness > score_partial.completeness
        assert score_partial.completeness > score_none.completeness


def test_convenience_functions():
    claims = [{"claim_text": "Standard claim text for testing purposes."}]
    results = enhance_claims(claims)
    assert len(results) == 1

    evidence = [
        {
            "evidence_text": "Evidence text with more than fifty characters to ensure it passes the length check."
        }
    ]
    results_ev = enhance_evidence(evidence)
    assert len(results_ev) == 1


def test_quality_score_to_dict():
    qs = QualityScore(overall=0.9, specificity=0.8)
    d = qs.to_dict()
    assert d["overall"] == 0.9
    assert d["specificity"] == 0.8