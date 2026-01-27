from pathlib import Path

import pytest


@pytest.mark.core
def test_pdf_parser(tmp_path):
    fitz = pytest.importorskip("fitz")
    from jarvis_core.ingestion.pdf_parser import parse_pdf

    pdf_path = Path(tmp_path) / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Sample Title\nAbstract: This is a test.\nINTRODUCTION\nBody text.\nREFERENCES\nRef 1")
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf(pdf_path)
    assert parsed.title == "Sample Title"
    assert "test" in parsed.abstract.lower()
    assert parsed.references
