from jarvis_core.evidence.v2_schema import EvidenceReport, Claim, Evidence, SupportSpan


def test_evidence_report_validation():
    # Valid report
    report = EvidenceReport(
        title="Test Report",
        summary="Summary text",
        claims=[
            Claim(
                statement="High confidence fact",
                evidence=[
                    Evidence(
                        source_url="http://example.com",
                        source_title="Study 1",
                        confidence=0.9,
                        spans=[SupportSpan(chunk_id="c1", char_range=(0, 10), text_snippet="fact")],
                    )
                ],
            )
        ],
    )
    assert report.validate_audit() == True


def test_evidence_report_rejection():
    # Report with claim having NO evidence
    report = EvidenceReport(
        title="Insecure Report",
        summary="Summary text",
        claims=[Claim(statement="Unbacked claim", evidence=[])],
    )
    # The requirement is that claims must have at least one piece of evidence
    assert report.validate_audit() == False
