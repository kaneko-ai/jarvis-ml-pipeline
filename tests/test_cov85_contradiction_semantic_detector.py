from __future__ import annotations

import builtins
import sys
import types

import numpy as np
import pytest

from jarvis_core.contradiction.schema import (
    Claim,
    ClaimPair,
    ContradictionResult,
    ContradictionType,
)
from jarvis_core.contradiction.semantic_detector import (
    SemanticConfig,
    SemanticContradictionDetector,
    SimpleEmbedder,
    detect_semantic_contradiction,
)


class _MapEmbedder:
    def __init__(self, mapping: dict[str, list[float]]) -> None:
        self.mapping = mapping

    def embed(self, text: str) -> np.ndarray:
        return np.array(self.mapping[text], dtype=float)


def _claim(claim_id: str, text: str) -> Claim:
    return Claim(claim_id=claim_id, text=text, paper_id="paper")


def test_embedder_falls_back_to_simple_on_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "jarvis_core.embeddings":
            raise ImportError("forced")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    detector = SemanticContradictionDetector()
    assert isinstance(detector.embedder, SimpleEmbedder)


def test_embedder_uses_sentence_transformer_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_mod = types.ModuleType("jarvis_core.embeddings")

    class FakeSentenceTransformerEmbedding:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def embed(self, text: str) -> np.ndarray:
            return np.array([1.0, 0.0])

    fake_mod.SentenceTransformerEmbedding = FakeSentenceTransformerEmbedding
    monkeypatch.setitem(sys.modules, "jarvis_core.embeddings", fake_mod)

    detector = SemanticContradictionDetector(config=SemanticConfig(model_name="fake-model"))
    embedder = detector.embedder
    assert isinstance(embedder, FakeSentenceTransformerEmbedding)
    assert embedder.model_name == "fake-model"


def test_detect_returns_none_when_similarity_below_threshold() -> None:
    detector = SemanticContradictionDetector()
    detector._embedder = _MapEmbedder({"a": [1.0, 0.0], "b": [0.0, 1.0]})

    result = detector.detect(_claim("1", "a"), _claim("2", "b"))
    assert result.contradiction_type == ContradictionType.NONE
    assert result.confidence == 1.0


def test_detect_returns_direct_when_negation_is_similar() -> None:
    detector = SemanticContradictionDetector()
    c1 = _claim("1", "Drug increases survival")
    c2 = _claim("2", "Drug decreases survival")
    negated = detector._negate_claim(c1.text)
    detector._embedder = _MapEmbedder(
        {
            c1.text: [1.0, 0.0],
            c2.text: [1.0, 0.0],
            negated: [1.0, 0.0],
        }
    )

    result = detector.detect(c1, c2)
    assert result.contradiction_type == ContradictionType.DIRECT
    assert result.scores["negation_similarity"] >= detector.config.similarity_threshold


def test_detect_returns_partial_when_partial_score_high() -> None:
    detector = SemanticContradictionDetector(
        config=SemanticConfig(use_negation_embedding=False, contradiction_threshold=0.3)
    )
    c1 = _claim("1", "treatment increase efficacy")
    c2 = _claim("2", "treatment decrease efficacy")
    detector._embedder = _MapEmbedder({c1.text: [1.0, 1.0], c2.text: [1.0, 1.0]})

    result = detector.detect(c1, c2)
    assert result.contradiction_type == ContradictionType.PARTIAL
    assert result.confidence == 0.8


def test_detect_returns_none_after_high_similarity_when_no_contradiction() -> None:
    detector = SemanticContradictionDetector(
        config=SemanticConfig(use_negation_embedding=False, contradiction_threshold=0.9)
    )
    c1 = _claim("1", "same trend and context")
    c2 = _claim("2", "same trend and context")
    detector._embedder = _MapEmbedder({c1.text: [1.0, 0.0], c2.text: [1.0, 0.0]})

    result = detector.detect(c1, c2)
    assert result.contradiction_type == ContradictionType.NONE


def test_detect_batch_collects_only_contradictory_pairs(monkeypatch: pytest.MonkeyPatch) -> None:
    detector = SemanticContradictionDetector()
    claims = [_claim("1", "a"), _claim("2", "b"), _claim("3", "c")]

    def _fake_detect(a: Claim, b: Claim) -> ContradictionResult:
        ctype = (
            ContradictionType.DIRECT
            if {a.claim_id, b.claim_id} == {"1", "2"}
            else ContradictionType.NONE
        )
        return ContradictionResult(
            claim_pair=ClaimPair(claim_a=a, claim_b=b),
            contradiction_type=ctype,
            confidence=0.9,
        )

    monkeypatch.setattr(detector, "detect", _fake_detect)
    result = detector.detect_batch(claims)
    assert len(result) == 1
    assert {result[0][0].claim_id, result[0][1].claim_id} == {"1", "2"}


def test_internal_helpers_and_simple_embedder() -> None:
    detector = SemanticContradictionDetector()

    assert detector._cosine_similarity(np.array([0.0, 0.0]), np.array([1.0, 1.0])) == 0.0
    assert detector._cosine_similarity(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == 1.0

    assert detector._negate_claim("Drug increases efficacy") == "drug decreases efficacy"
    assert detector._negate_claim("No mapped term here").startswith("It is not the case")

    partial = detector._check_partial_contradiction(
        _claim("a", "results show more benefit"),
        _claim("b", "results show less harm"),
    )
    assert partial == 0.8
    none = detector._check_partial_contradiction(
        _claim("a", "same direction"), _claim("b", "same direction")
    )
    assert none == 0.0

    vector = SimpleEmbedder().embed("alpha beta alpha")
    assert vector.shape[0] == 1000
    assert float(np.linalg.norm(vector)) == pytest.approx(1.0, rel=1e-6)


def test_convenience_wrapper_detect_semantic_contradiction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = SemanticConfig(use_negation_embedding=False)
    c1 = _claim("1", "x")
    c2 = _claim("2", "y")

    def _fake_detect(self, claim_a: Claim, claim_b: Claim) -> ContradictionResult:
        return ContradictionResult(
            claim_pair=ClaimPair(claim_a=claim_a, claim_b=claim_b),
            contradiction_type=ContradictionType.NONE,
            confidence=0.5,
        )

    monkeypatch.setattr(SemanticContradictionDetector, "detect", _fake_detect)
    result = detect_semantic_contradiction(c1, c2, config=cfg)
    assert isinstance(result, ContradictionResult)
    assert result.contradiction_type == ContradictionType.NONE
    assert result.confidence == 0.5
