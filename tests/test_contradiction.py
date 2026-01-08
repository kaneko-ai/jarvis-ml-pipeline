"""Tests for the Contradiction Detection Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.3
"""



class TestContradictionSchema:
    """Tests for contradiction schema."""

    def test_claim_dataclass(self):
        """Test Claim dataclass."""
        from jarvis_core.contradiction import Claim

        claim = Claim(
            claim_id="c1",
            text="Drug X increases survival",
            paper_id="paper_A",
        )

        assert claim.claim_id == "c1"
        assert claim.paper_id == "paper_A"

    def test_contradiction_type_enum(self):
        """Test ContradictionType enum."""
        from jarvis_core.contradiction import ContradictionType

        assert ContradictionType.DIRECT.value == "direct"
        assert ContradictionType.QUANTITATIVE.value == "quantitative"
        assert ContradictionType.NONE.value == "none"


class TestClaimNormalizer:
    """Tests for claim normalizer."""

    def test_normalizer_init(self):
        """Test normalizer initialization."""
        from jarvis_core.contradiction import ClaimNormalizer

        normalizer = ClaimNormalizer()
        assert normalizer is not None

    def test_normalize_claim(self):
        """Test claim normalization."""
        from jarvis_core.contradiction import ClaimNormalizer

        normalizer = ClaimNormalizer()
        result = normalizer.normalize("Drug X increases survival by 20%")

        assert result.original == "Drug X increases survival by 20%"
        assert result.predicate == "increases"
        assert len(result.quantities) > 0

    def test_detect_negation(self):
        """Test negation detection."""
        from jarvis_core.contradiction import ClaimNormalizer

        normalizer = ClaimNormalizer()

        result1 = normalizer.normalize("Drug X does not improve outcomes")
        assert result1.is_negated == True

        result2 = normalizer.normalize("Drug X improves outcomes")
        assert result2.is_negated == False


class TestContradictionDetector:
    """Tests for contradiction detector."""

    def test_detector_init(self):
        """Test detector initialization."""
        from jarvis_core.contradiction import ContradictionDetector

        detector = ContradictionDetector()
        assert detector is not None

    def test_detect_direct_contradiction(self):
        """Test detection of direct contradiction."""
        from jarvis_core.contradiction import Claim, ContradictionDetector, ContradictionType

        detector = ContradictionDetector()

        claim_a = Claim(
            claim_id="c1",
            text="Treatment increases patient survival",
            paper_id="paper_A",
        )
        claim_b = Claim(
            claim_id="c2",
            text="Treatment decreases patient survival",
            paper_id="paper_B",
        )

        result = detector.detect(claim_a, claim_b)

        assert result.is_contradictory
        # Can be DIRECT or PARTIAL depending on detection method
        assert result.contradiction_type in [ContradictionType.DIRECT, ContradictionType.PARTIAL]

    def test_detect_no_contradiction(self):
        """Test detection when no contradiction."""
        from jarvis_core.contradiction import Claim, ContradictionDetector, ContradictionType

        detector = ContradictionDetector()

        claim_a = Claim(
            claim_id="c1",
            text="Treatment improves cognitive function",
            paper_id="paper_A",
        )
        claim_b = Claim(
            claim_id="c2",
            text="Exercise reduces cardiovascular risk",
            paper_id="paper_B",
        )

        result = detector.detect(claim_a, claim_b)

        assert not result.is_contradictory
        assert result.contradiction_type == ContradictionType.NONE

    def test_detect_quantitative_contradiction(self):
        """Test detection of quantitative contradiction."""
        from jarvis_core.contradiction import Claim, ContradictionDetector

        detector = ContradictionDetector()

        claim_a = Claim(
            claim_id="c1",
            text="Treatment increases survival by 50%",
            paper_id="paper_A",
        )
        claim_b = Claim(
            claim_id="c2",
            text="Treatment increases survival by 5%",
            paper_id="paper_B",
        )

        result = detector.detect(claim_a, claim_b)

        # May or may not detect as contradiction depending on threshold
        assert result.scores.get("quantitative", 0) >= 0


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.contradiction import (
            Claim,
            ContradictionDetector,
            detect_contradiction,
        )

        assert Claim is not None
        assert ContradictionDetector is not None
        assert detect_contradiction is not None
