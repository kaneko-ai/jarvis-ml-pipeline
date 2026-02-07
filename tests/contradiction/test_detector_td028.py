"""TD-028: Contradiction detection quality tests.

実世界の矛盾シナリオを検証するテスト。TD-006 の前提基盤。
既存テストは変更しない。
"""

import pytest

from jarvis_core.contradiction.detector import ContradictionDetector
from jarvis_core.contradiction.normalizer import ClaimNormalizer
from jarvis_core.contradiction.schema import Claim


@pytest.fixture
def detector() -> ContradictionDetector:
    return ContradictionDetector()


@pytest.fixture
def normalizer() -> ClaimNormalizer:
    return ClaimNormalizer()


class TestContradictoryClaims:
    def test_increase_vs_decrease(self, detector: ContradictionDetector) -> None:
        a = Claim(claim_id="1", text="Drug X increases survival rate", paper_id="A")
        b = Claim(claim_id="2", text="Drug X decreases survival rate", paper_id="B")
        result = detector.detect([a.text, b.text])
        assert len(result) > 0

    def test_effective_vs_not_effective(self, detector: ContradictionDetector) -> None:
        a = Claim(claim_id="1", text="Treatment A is effective for pain", paper_id="A")
        b = Claim(claim_id="2", text="Treatment A is ineffective for pain", paper_id="B")
        result = detector.detect([a.text, b.text])
        assert len(result) > 0


class TestNonContradictoryClaims:
    def test_synonymous_positive(self, detector: ContradictionDetector) -> None:
        a = Claim(claim_id="1", text="Drug X improves outcomes", paper_id="A")
        b = Claim(claim_id="2", text="Drug X shows positive effects", paper_id="B")
        result = detector.detect([a.text, b.text])
        assert len(result) == 0

    def test_different_topics(self, detector: ContradictionDetector) -> None:
        a = Claim(claim_id="1", text="Drug X reduces blood pressure", paper_id="A")
        b = Claim(claim_id="2", text="Exercise improves cardiovascular health", paper_id="B")
        result = detector.detect([a.text, b.text])
        assert len(result) == 0


class TestNormalization:
    def test_negation_detected(self, normalizer: ClaimNormalizer) -> None:
        result = normalizer.normalize("Drug X does not improve survival")
        assert result.is_negated is True

    def test_empty_string(self, normalizer: ClaimNormalizer) -> None:
        result = normalizer.normalize("")
        assert result.normalized == ""

    def test_quantity_extraction(self, normalizer: ClaimNormalizer) -> None:
        result = normalizer.normalize("Reduced mortality by 15%")
        assert len(result.quantities) > 0
        assert result.quantities[0][0] == 15.0

    def test_same_topic_detection(self, normalizer: ClaimNormalizer) -> None:
        a = Claim(claim_id="1", text="Aspirin reduces heart attack risk", paper_id="A")
        b = Claim(claim_id="2", text="Aspirin increases heart attack risk", paper_id="B")
        assert normalizer.are_about_same_topic(a, b) is True
