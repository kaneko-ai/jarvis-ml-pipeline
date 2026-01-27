"""Bibliography Export.

Per RP-24, provides BibTeX and CSL-JSON export.
"""

from __future__ import annotations

import json
from typing import List

from .models import PaperRecord


def to_bibtex(paper: PaperRecord) -> str:
    """Convert PaperRecord to BibTeX entry."""
    # Generate citation key
    first_author = paper.authors[0].split()[-1] if paper.authors else "Unknown"
    year = paper.pubdate[:4] if paper.pubdate else "XXXX"
    key = f"{first_author}{year}"

    authors = " and ".join(paper.authors) if paper.authors else "Unknown"

    lines = [
        f"@article{{{key},",
        f"  title = {{{paper.title}}},",
        f"  author = {{{authors}}},",
    ]

    if paper.journal:
        lines.append(f"  journal = {{{paper.journal}}},")
    if paper.pubdate:
        lines.append(f"  year = {{{year}}},")
    if paper.doi:
        lines.append(f"  doi = {{{paper.doi}}},")
    if paper.pmid:
        lines.append(f"  pmid = {{{paper.pmid}}},")

    lines.append("}")

    return "\n".join(lines)


def to_csl_json(paper: PaperRecord) -> dict:
    """Convert PaperRecord to CSL-JSON entry."""
    first_author = paper.authors[0].split()[-1] if paper.authors else "Unknown"
    year = paper.pubdate[:4] if paper.pubdate else "XXXX"

    entry = {
        "id": f"{first_author}{year}",
        "type": "article-journal",
        "title": paper.title,
    }

    if paper.authors:
        entry["author"] = [{"literal": author} for author in paper.authors]

    if paper.journal:
        entry["container-title"] = paper.journal

    if paper.pubdate:
        entry["issued"] = {"date-parts": [[int(year)]]}

    if paper.doi:
        entry["DOI"] = paper.doi

    if paper.pmid:
        entry["PMID"] = paper.pmid

    return entry


def export_bibtex(papers: List[PaperRecord], output_path: str) -> None:
    """Export papers to BibTeX file."""
    entries = [to_bibtex(p) for p in papers]
    content = "\n\n".join(entries)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def export_csl_json(papers: List[PaperRecord], output_path: str) -> None:
    """Export papers to CSL-JSON file."""
    entries = [to_csl_json(p) for p in papers]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
