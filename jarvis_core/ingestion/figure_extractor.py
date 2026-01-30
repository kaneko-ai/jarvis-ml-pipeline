"""Extract figures from PDF documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Figure:
    image_bytes: bytes
    caption: str | None
    page_number: int


def extract_figures(pdf_path: Path) -> list[Figure]:
    """Extract figures from PDF using PyMuPDF.

    Extracted images are saved under a `figures/` directory next to the PDF.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("PyMuPDF is required for figure extraction") from exc

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    figures: list[Figure] = []
    output_dir = pdf_path.parent / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    for page_index, page in enumerate(doc, start=1):
        for image_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            image_bytes = pix.tobytes("png")
            filename = output_dir / f"page_{page_index}_img_{image_index + 1}.png"
            filename.write_bytes(image_bytes)
            figures.append(Figure(image_bytes=image_bytes, caption=None, page_number=page_index))
            pix = None

    doc.close()
    return figures