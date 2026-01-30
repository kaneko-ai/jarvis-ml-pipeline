from jarvis_core.report.citation_audit import CitationAuditor


def test_citation_audit_valid():
    auditor = CitationAuditor()
    text = "Studies show that T-cells are important [1]. Another study confirms this [2]."
    valid_ids = ["1", "2"]

    result = auditor.audit(text, valid_ids)

    assert result.is_valid
    assert len(result.hallucinated_citations) == 0
    assert result.score == 1.0  # All sentences cited


def test_citation_audit_hallucination():
    auditor = CitationAuditor()
    text = "This is a claimed fact [99]."
    valid_ids = ["1", "2"]

    result = auditor.audit(text, valid_ids)

    assert not result.is_valid
    assert "99" in result.hallucinated_citations


def test_citation_audit_missing():
    auditor = CitationAuditor()
    text = "This is a claim without citation. This is another claim without citation."
    valid_ids = ["1"]

    result = auditor.audit(text, valid_ids)

    # Depending on threshold, this might fail or pass but lower score
    # Our threshold is 0.5 score
    # 2 sentences, 0 cited -> score 0.0
    assert not result.is_valid
    assert result.score == 0.0
    assert len(result.missing_citations) > 0