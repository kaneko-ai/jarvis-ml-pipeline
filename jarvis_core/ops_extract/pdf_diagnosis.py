"""PDF type diagnosis for ops_extract ingestion."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contracts import OPS_EXTRACT_SCHEMA_VERSION


@dataclass(frozen=True)
class PdfDiagnosis:
    file: str
    type: str
    page_count: int
    text_pages: int
    image_pages: int
    encrypted: bool
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _page_has_image(page: Any) -> bool:
    try:
        resources = page.get("/Resources")
        if resources is None:
            return False
        xobj_ref = resources.get("/XObject")
        if xobj_ref is None:
            return False
        xobj = xobj_ref.get_object()
        for _, obj in xobj.items():
            target = obj.get_object()
            if str(target.get("/Subtype", "")) == "/Image":
                return True
    except Exception:
        return False
    return False


def diagnose_pdf(path: Path) -> PdfDiagnosis:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
    except Exception as exc:
        return PdfDiagnosis(
            file=str(path),
            type="corrupted",
            page_count=0,
            text_pages=0,
            image_pages=0,
            encrypted=False,
            error=str(exc),
        )

    try:
        encrypted = bool(getattr(reader, "is_encrypted", False))
        if encrypted:
            return PdfDiagnosis(
                file=str(path),
                type="encrypted",
                page_count=len(reader.pages),
                text_pages=0,
                image_pages=0,
                encrypted=True,
                error="",
            )

        page_count = len(reader.pages)
        text_pages = 0
        image_pages = 0
        for page in reader.pages:
            try:
                text = (page.extract_text() or "").strip()
            except Exception:
                text = ""
            if text:
                text_pages += 1
            if _page_has_image(page):
                image_pages += 1

        if text_pages > 0 and image_pages > 0:
            category = "hybrid"
        elif text_pages > 0:
            category = "text-embedded"
        elif page_count > 0:
            category = "image-only"
        else:
            category = "corrupted"

        return PdfDiagnosis(
            file=str(path),
            type=category,
            page_count=page_count,
            text_pages=text_pages,
            image_pages=image_pages,
            encrypted=False,
            error="",
        )
    except Exception as exc:
        return PdfDiagnosis(
            file=str(path),
            type="corrupted",
            page_count=0,
            text_pages=0,
            image_pages=0,
            encrypted=False,
            error=str(exc),
        )


def diagnose_pdfs(paths: list[Path]) -> dict[str, Any]:
    items = [diagnose_pdf(path).to_dict() for path in paths]
    summary = {
        "text-embedded": 0,
        "image-only": 0,
        "hybrid": 0,
        "encrypted": 0,
        "corrupted": 0,
    }
    for item in items:
        key = str(item.get("type", "corrupted"))
        if key not in summary:
            key = "corrupted"
        summary[key] += 1
    return {
        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
        "files": items,
        "summary": summary,
    }
