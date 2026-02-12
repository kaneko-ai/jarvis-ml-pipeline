from __future__ import annotations

from pathlib import Path

import pytest

from jarvis_core.evidence.locator_verify import (
    extract_text_from_pdf,
    levenshtein_ratio,
    verify_all_evidence,
    verify_locator,
)


def test_levenshtein_ratio_edge_cases() -> None:
    assert levenshtein_ratio("abc", "abc") == 1.0
    assert levenshtein_ratio("", "abc") == 0.0
    assert 0.0 < levenshtein_ratio("abc", "abd") < 1.0


def test_extract_text_from_pdf_placeholder_returns_empty(tmp_path: Path) -> None:
    result = extract_text_from_pdf(tmp_path / "x.pdf", page=1)
    assert result == ""


def test_verify_locator_error_paths(tmp_path: Path) -> None:
    assert verify_locator({"paper_id": "p1"}, tmp_path)["error"] == "No locator provided"

    no_quote = verify_locator({"paper_id": "p1", "locator": {"page": 1}}, tmp_path)
    assert no_quote["error"] == "No quote_span provided"

    missing_pdf = verify_locator(
        {"paper_id": "p1", "locator": {"page": 1}, "quote_span": "abc"},
        tmp_path,
    )
    assert "PDF not found" in missing_pdf["error"]


def test_verify_locator_success_and_low_similarity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf_path = tmp_path / "paper-1.pdf"
    pdf_path.write_bytes(b"pdf")

    monkeypatch.setattr(
        "jarvis_core.evidence.locator_verify.extract_text_from_pdf",
        lambda *args, **kwargs: "same quote",
    )
    ok = verify_locator(
        {
            "paper_id": "paper-1",
            "locator": {"page": 2, "paragraph": 3, "sentence": 1},
            "quote_span": "same quote",
        },
        tmp_path,
    )
    assert ok["valid"] is True
    assert ok["error"] is None

    monkeypatch.setattr(
        "jarvis_core.evidence.locator_verify.extract_text_from_pdf",
        lambda *args, **kwargs: "different",
    )
    ng = verify_locator(
        {"paper_id": "paper-1", "locator": {"page": 1}, "quote_span": "totally unrelated"},
        tmp_path,
    )
    assert ng["valid"] is False
    assert "Low similarity" in ng["error"]


def test_verify_locator_extraction_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf_path = tmp_path / "p2.pdf"
    pdf_path.write_bytes(b"pdf")

    def _raise(*args, **kwargs):  # noqa: ANN001, ANN002
        raise RuntimeError("boom")

    monkeypatch.setattr("jarvis_core.evidence.locator_verify.extract_text_from_pdf", _raise)

    result = verify_locator(
        {"paper_id": "p2", "locator": {"page": 1}, "quote_span": "x"},
        tmp_path,
    )
    assert result["valid"] is False
    assert "Extraction failed" in result["error"]


def test_verify_all_evidence_counts_invalid_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fake_verify(ev: dict, _pdf_dir: Path) -> dict:
        if ev.get("evidence_id") == "ok":
            return {"valid": True, "error": None, "similarity": 1.0}
        return {"valid": False, "error": "bad", "similarity": 0.2}

    monkeypatch.setattr("jarvis_core.evidence.locator_verify.verify_locator", _fake_verify)

    report = verify_all_evidence(
        [{"evidence_id": "ok"}, {"evidence_id": "ng"}, {"paper_id": "x"}],
        tmp_path,
    )
    assert report["total"] == 3
    assert report["valid_count"] == 1
    assert report["invalid_count"] == 2
    assert report["validity_rate"] == 1 / 3
    assert report["invalid_ids"][0]["evidence_id"] == "ng"
    assert report["invalid_ids"][1]["evidence_id"] == "unknown"
