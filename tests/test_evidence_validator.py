"""Tests for evidence validator."""

from jarvis_core.evidence.store import EvidenceStore
from jarvis_core.evidence.validator import EvidenceValidator


def test_missing_evidence_ids():
    store = EvidenceStore()
    validator = EvidenceValidator()

    result = validator.validate_conclusion("Test conclusion", [], store)

    assert result.is_valid is False
    assert "MISSING_EVIDENCE_ID" in result.violations
    assert result.uncertainty_label == "推測"


def test_valid_evidence_id():
    store = EvidenceStore()
    validator = EvidenceValidator()

    chunk_id = store.add_chunk("local", "page:1", "Evidence text")
    result = validator.validate_conclusion("Test", [chunk_id], store)

    assert result.is_valid is True
    assert result.violations == []


def test_invalid_evidence_id():
    store = EvidenceStore()
    validator = EvidenceValidator()

    result = validator.validate_conclusion("Test", ["missing-id"], store)

    assert result.is_valid is False
    assert "INVALID_EVIDENCE_ID" in result.violations


def test_mixed_evidence_ids():
    store = EvidenceStore()
    validator = EvidenceValidator()

    chunk_id = store.add_chunk("local", "page:2", "Evidence text")
    result = validator.validate_conclusion("Test", [chunk_id, "bad-id"], store)

    assert result.is_valid is False
    assert "INVALID_EVIDENCE_ID" in result.violations


def test_uncertainty_label_included():
    store = EvidenceStore()
    validator = EvidenceValidator()

    chunk_id = store.add_chunk("local", "page:3", "Evidence text")
    result = validator.validate_conclusion("Test", [chunk_id], store)

    assert isinstance(result.uncertainty_label, str)