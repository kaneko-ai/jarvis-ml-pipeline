"""BibTeX export for paper search results (P1-3)."""

from __future__ import annotations

import re
from pathlib import Path


def papers_to_bibtex(papers: list[dict]) -> str:
    """Convert paper list to BibTeX format string."""
    entries = []
    for i, p in enumerate(papers, 1):
        entry = _paper_to_bibtex_entry(p, i)
        if entry:
            entries.append(entry)
    return "\n\n".join(entries) + "\n"


def save_bibtex(papers: list[dict], output_path: Path) -> None:
    """Save papers as .bib file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = papers_to_bibtex(papers)
    output_path.write_text(content, encoding="utf-8")


def _paper_to_bibtex_entry(paper: dict, index: int) -> str:
    """Convert a single paper dict to a BibTeX entry."""
    source = paper.get("source", "unknown")
    source_id = paper.get("source_id", "")
    title = paper.get("title", "Untitled")
    authors = paper.get("authors", [])
    year = paper.get("year", 0)
    journal = paper.get("journal", "")
    doi = paper.get("doi", "")
    pmid = paper.get("pmid", "")
    abstract = paper.get("abstract", "")
    url = paper.get("url", "")

    # Generate cite key: AuthorYear or source_index
    cite_key = _make_cite_key(authors, year, index)

    # Format authors for BibTeX: "Last1, First1 and Last2, First2"
    author_str = " and ".join(authors) if authors else "Unknown"

    lines = [f"@article{{{cite_key},"]
    lines.append(f"  title = {{{title}}},")
    lines.append(f"  author = {{{author_str}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if journal:
        lines.append(f"  journal = {{{journal}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    if pmid:
        lines.append(f"  pmid = {{{pmid}}},")
    if url:
        lines.append(f"  url = {{{url}}},")
    if abstract:
        clean = abstract.replace("{", "").replace("}", "")
        if len(clean) > 500:
            clean = clean[:500] + "..."
        lines.append(f"  abstract = {{{clean}}},")

    lines.append("}")
    return "\n".join(lines)


def _make_cite_key(authors: list[str], year: int, index: int) -> str:
    """Generate a BibTeX cite key like 'Keir2008' or 'paper_1'."""
    if authors and year:
        first = authors[0]
        # Extract last name (take first word)
        last = first.split(",")[0].split()[-1] if first else "Unknown"
        # Remove non-alphanumeric
        last = re.sub(r"[^a-zA-Z]", "", last)
        return f"{last}{year}"
    return f"paper_{index}"