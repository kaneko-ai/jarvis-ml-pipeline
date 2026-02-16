"""BibTeX generation utilities."""

from __future__ import annotations


def to_bibtex(entry: dict) -> str:
    key = _bib_key(entry)
    title = _escape(entry.get("title", "Untitled"))
    journal = _escape(entry.get("journal", ""))
    year = str(entry.get("pub_date", ""))[:4]
    doi = _escape(entry.get("doi", ""))
    return (
        f"@article{{{key},\n"
        f"  title = {{{title}}},\n"
        f"  journal = {{{journal}}},\n"
        f"  year = {{{year}}},\n"
        f"  doi = {{{doi}}}\n"
        f"}}\n"
    )


def _bib_key(entry: dict) -> str:
    doi = str(entry.get("doi") or "").strip()
    if doi:
        return doi.replace("/", "_").replace(".", "_")
    pmid = str(entry.get("pmid") or "unknown")
    return f"pmid_{pmid}"


def _escape(value: object) -> str:
    return str(value).replace("{", "\\{").replace("}", "\\}")
