from pathlib import Path
import base64

import pytest


@pytest.mark.core
def test_figure_extractor(tmp_path):
    fitz = pytest.importorskip("fitz")
    from jarvis_core.ingestion.figure_extractor import extract_figures

    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+yv8cAAAAASUVORK5CYII="
    )

    pdf_path = Path(tmp_path) / "figures.pdf"
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 100, 100)
    page.insert_image(rect, stream=png_bytes)
    doc.save(pdf_path)
    doc.close()

    figures = extract_figures(pdf_path)
    assert figures
    assert (tmp_path / "figures").exists()
