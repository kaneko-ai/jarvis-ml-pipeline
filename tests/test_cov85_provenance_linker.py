"""Coverage tests for jarvis_core.provenance.linker."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jarvis_core.provenance.linker import (
    ChunkInfo,
    ProvenanceError,
    ProvenanceLinker,
    ProvenanceValidator,
    get_provenance_linker,
    get_provenance_validator,
)


class TestChunkInfo:
    def test_fields(self) -> None:
        ci = ChunkInfo(doc_id="d1", section="Methods", chunk_id="ch1", text="hello", start=0, end=5)
        assert ci.doc_id == "d1"
        assert ci.text == "hello"


class TestProvenanceLinker:
    def test_init_defaults(self) -> None:
        linker = ProvenanceLinker()
        assert linker.strict is True
        assert linker.min_confidence == 0.5

    def test_register_chunk(self) -> None:
        linker = ProvenanceLinker()
        linker.register_chunk("d1", "Methods", "ch1", "text here", 0, 9)
        assert "ch1" in linker.chunks

    def test_register_chunk_auto_end(self) -> None:
        linker = ProvenanceLinker()
        linker.register_chunk("d1", "Methods", "ch1", "text")
        assert linker.chunks["ch1"].end == 4

    def test_register_chunks_from_document(self) -> None:
        linker = ProvenanceLinker()
        sections = {"Methods": "A" * 1200, "Results": "B" * 300}
        ids = linker.register_chunks_from_document("d1", sections, chunk_size=500, overlap=50)
        assert len(ids) >= 3  # Methods 3 chunks + Results 1 chunk

    def test_generate_chunk_id(self) -> None:
        linker = ProvenanceLinker()
        cid = linker._generate_chunk_id("d1", "Methods", 0)
        assert isinstance(cid, str)
        assert len(cid) == 12

    def test_find_evidence_no_chunks(self) -> None:
        linker = ProvenanceLinker()
        assert linker.find_evidence("claim text") == []

    def test_find_evidence_match(self) -> None:
        linker = ProvenanceLinker()
        linker.register_chunk("d1", "Methods", "ch1", "randomized controlled trial was conducted for cancer treatment")
        evidence = linker.find_evidence("randomized controlled trial was conducted for cancer treatment")
        assert len(evidence) >= 1
        assert evidence[0].confidence > 0

    def test_find_evidence_no_match(self) -> None:
        linker = ProvenanceLinker()
        linker.register_chunk("d1", "Methods", "ch1", "completely different topic about physics quarks")
        evidence = linker.find_evidence("machine learning neural networks deep")
        assert len(evidence) == 0

    def test_find_evidence_empty_chunk(self) -> None:
        linker = ProvenanceLinker()
        linker.register_chunk("d1", "Methods", "ch1", "")
        evidence = linker.find_evidence("any claim")
        assert len(evidence) == 0

    def test_tokenize(self) -> None:
        linker = ProvenanceLinker()
        tokens = linker._tokenize("Hello, World! This is a test.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "a" not in tokens  # < 3 chars

    def test_find_span_exact_match(self) -> None:
        linker = ProvenanceLinker()
        start, end = linker._find_span("hello", "prefix hello suffix")
        assert start == 7

    def test_find_span_partial_match(self) -> None:
        linker = ProvenanceLinker()
        start, end = linker._find_span("hello world. another sentence.", "prefix hello world suffix")
        assert start >= 0

    def test_find_span_no_match(self) -> None:
        linker = ProvenanceLinker()
        start, end = linker._find_span("zzzzz", "yyyyy")
        assert start == 0
        assert end == 5

    def test_create_claim_auto_link(self) -> None:
        linker = ProvenanceLinker()
        linker.register_chunk("d1", "M", "ch1", "cancer treatment showed improvement in patients overall")
        claim = linker.create_claim("c1", "cancer treatment showed improvement in patients overall", "fact")
        assert claim.claim_id == "c1"
        assert len(claim.evidence) >= 1

    def test_create_claim_no_auto_link(self) -> None:
        linker = ProvenanceLinker()
        claim = linker.create_claim("c1", "some claim", auto_link=False)
        assert len(claim.evidence) == 0

    def test_create_claim_strict_no_evidence(self) -> None:
        linker = ProvenanceLinker(strict=True)
        claim = linker.create_claim("c1", "no evidence claim here xyz abc")
        assert claim.claim_type == "hypothesis"
        assert claim.confidence == 0.0

    def test_create_claim_non_strict(self) -> None:
        linker = ProvenanceLinker(strict=False)
        claim = linker.create_claim("c1", "no evidence claim here xyz abc")
        assert claim.claim_type == "fact"  # Not downgraded

    def test_validate_claims_empty(self) -> None:
        linker = ProvenanceLinker()
        passed, rate, warnings = linker.validate_claims([])
        assert passed is False
        assert rate == 0.0

    def test_validate_claims_all_evidenced(self) -> None:
        linker = ProvenanceLinker()
        c = MagicMock()
        c.has_evidence.return_value = True
        c.claim_id = "c1"
        passed, rate, warnings = linker.validate_claims([c])
        assert passed is True
        assert rate == 1.0

    def test_validate_claims_some_missing(self) -> None:
        linker = ProvenanceLinker()
        c1 = MagicMock()
        c1.has_evidence.return_value = True
        c1.claim_id = "c1"
        c2 = MagicMock()
        c2.has_evidence.return_value = False
        c2.claim_id = "c2"
        passed, rate, warnings = linker.validate_claims([c1, c2])
        assert passed is False
        assert len(warnings) == 1

    def test_attach_evidence(self) -> None:
        linker = ProvenanceLinker()
        claim = MagicMock()
        claim.evidence = []
        ev = MagicMock()
        ev.confidence = 0.8
        result = linker.attach_evidence(claim, [ev])
        assert len(result.evidence) == 1
        assert result.confidence == 0.8

    def test_get_missing_evidence_claims(self) -> None:
        linker = ProvenanceLinker()
        c1 = MagicMock()
        c1.has_evidence.return_value = True
        c2 = MagicMock()
        c2.has_evidence.return_value = False
        result = linker.get_missing_evidence_claims([c1, c2])
        assert len(result) == 1


class TestProvenanceValidator:
    def test_validate_empty(self) -> None:
        validator = ProvenanceValidator()
        result = validator.validate([])
        assert result["passed"] is False

    def test_validate_all_evidenced(self) -> None:
        validator = ProvenanceValidator()
        c = MagicMock()
        c.has_evidence.return_value = True
        c.claim_type = "fact"
        c.claim_id = "c1"
        result = validator.validate([c])
        assert result["passed"] is True

    def test_validate_fact_without_evidence(self) -> None:
        validator = ProvenanceValidator(reject_assertions_without_evidence=True)
        c = MagicMock()
        c.has_evidence.return_value = False
        c.claim_type = "fact"
        c.claim_id = "c1"
        result = validator.validate([c])
        assert result["passed"] is False
        assert result["facts_without_evidence"] == 1

    def test_validate_hypothesis_without_evidence(self) -> None:
        validator = ProvenanceValidator(min_rate=0.0)
        c = MagicMock()
        c.has_evidence.return_value = False
        c.claim_type = "hypothesis"
        c.claim_id = "c1"
        result = validator.validate([c])
        assert "WARNING" in result["issues"][0]


class TestFactoryFunctions:
    def test_get_provenance_linker(self) -> None:
        linker = get_provenance_linker()
        assert isinstance(linker, ProvenanceLinker)
        assert linker.strict is True
        assert linker.min_confidence == 0.5

    def test_get_provenance_linker_non_strict(self) -> None:
        linker = get_provenance_linker(strict=False)
        assert linker.strict is False

    def test_get_provenance_validator(self) -> None:
        validator = get_provenance_validator()
        assert isinstance(validator, ProvenanceValidator)
        assert validator.min_rate == 0.95
        assert validator.reject_assertions is True

    def test_get_provenance_validator_custom(self) -> None:
        validator = get_provenance_validator(min_rate=0.5)
        assert validator.min_rate == 0.5
