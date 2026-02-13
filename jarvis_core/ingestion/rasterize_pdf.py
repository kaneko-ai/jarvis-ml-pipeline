"""PDF rasterization utility for OCR workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def rasterize_pdf_to_images(
    *,
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 300,
    image_format: str = "png",
) -> dict[str, Any]:
    """Render PDF pages to image files using PyMuPDF."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        import fitz
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PyMuPDF (fitz) is required for rasterization") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[str] = []

    doc = fitz.open(pdf_path)
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            page_path = output_dir / f"page_{i + 1:04d}.{image_format}"
            pix.save(page_path)
            image_paths.append(str(page_path))
    finally:
        doc.close()

    return {
        "pdf_path": str(pdf_path),
        "output_dir": str(output_dir),
        "dpi": dpi,
        "image_format": image_format,
        "page_count": len(image_paths),
        "image_paths": image_paths,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "pymupdf",
    }
