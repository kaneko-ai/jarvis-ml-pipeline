from __future__ import annotations

from jarvis_core.metadata.normalize import (
    audit_records,
    normalize_doi,
    normalize_record,
    normalize_title,
)


def test_normalize_helpers_and_record() -> None:
    assert normalize_doi(" 10.1000/XYZ ") == "10.1000/xyz"
    assert normalize_title("  A/B: Trial, Results!  ") == "a b trial results"

    record = normalize_record(
        {
            "title": "  Title ",
            "abstract": "  Abs ",
            "journal": "  J ",
            "doi": " DOI ",
            "pmid": " 1 ",
            "pmcid": " 2 ",
        }
    )
    assert record["title"] == "Title"
    assert record["abstract"] == "Abs"
    assert record["journal"] == "J"
    assert record["doi"] == "doi"
    assert record["pmid"] == "1"
    assert record["pmcid"] == "2"


def test_audit_records_flags_conflict_and_summary() -> None:
    papers = [
        {
            "title": "Alpha Study",
            "abstract": "x",
            "journal": "J1",
            "doi": "10.1/abc",
            "pmid": "1",
            "pmcid": "2",
            "year": 2099,
            "pdf_url": "",
            "fulltext_url": "",
        },
        {
            "title": "Beta Study",
            "abstract": "",
            "journal": "",
            "doi": "10.1/ABC",
            "pmid": "",
            "pmcid": "",
            "year": -1,
        },
    ]

    normalized, summary = audit_records(papers)

    assert "doi_title_conflict" in normalized[0]["audit_flags"]
    assert "year_out_of_range" in normalized[0]["audit_flags"]
    assert "missing_pdf_url" in normalized[0]["audit_flags"]
    assert "missing_fulltext_url" in normalized[0]["audit_flags"]

    second_flags = normalized[1]["audit_flags"]
    assert "missing_pmid" in second_flags
    assert "missing_pmcid" in second_flags
    assert "missing_journal" in second_flags
    assert "missing_abstract" in second_flags

    assert normalized[0]["audit_score"] <= 100
    assert summary["total_papers"] == 2
    assert summary["conflict_count"] == 2
    assert summary["missing_rates"]["missing_pmid"] == 0.5
