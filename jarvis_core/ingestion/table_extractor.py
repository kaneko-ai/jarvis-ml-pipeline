"""Extract tables from PDF or HTML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Table:
    headers: list[str]
    rows: list[list[str]]
    caption: str | None = None


def extract_tables(content: str | Path) -> list[Table]:
    """Extract tables from a PDF path or HTML string."""
    if isinstance(content, Path) or (
        isinstance(content, str) and Path(content).suffix.lower() == ".pdf"
    ):
        return _extract_from_pdf(Path(content))
    return _extract_from_html(content)


def _extract_from_pdf(pdf_path: Path) -> list[Table]:
    try:
        import tabula  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("tabula is required for PDF table extraction") from exc

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    dfs = tabula.read_pdf(str(pdf_path), pages="all")
    tables: list[Table] = []
    for df in dfs:
        headers = [str(h) for h in df.columns]
        rows = [[str(cell) for cell in row] for row in df.values.tolist()]
        tables.append(Table(headers=headers, rows=rows, caption=None))
    return tables


def _extract_from_html(html: str) -> list[Table]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("beautifulsoup4 is required for HTML table extraction") from exc

    soup = BeautifulSoup(html, "html.parser")
    tables: list[Table] = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = []
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if cells:
                rows.append(cells)
        caption_tag = table.find("caption")
        caption = caption_tag.get_text(strip=True) if caption_tag else None
        tables.append(Table(headers=headers, rows=rows, caption=caption))
    return tables