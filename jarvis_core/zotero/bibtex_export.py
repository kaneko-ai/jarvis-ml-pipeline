"""BibTeX export for Zotero."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jarvis_core.notes.note_generator import _load_jsonl


def _slugify(text: str, max_len: int = 32) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", text.strip())
    cleaned = cleaned.strip("_")
    return cleaned[:max_len] or "untitled"


def _journal_short(journal: str) -> str:
    return _slugify(journal, max_len=12) if journal else "Journal"


def _first_author(authors: Any) -> str:
    if isinstance(authors, list) and authors:
        first = authors[0]
    elif isinstance(authors, str):
        first = authors.split(";")[0]
    else:
        return "Unknown"
    if "," in first:
        return first.split(",")[0].strip()
    parts = first.split()
    return parts[-1] if parts else "Unknown"


def safe_key(paper: dict[str, Any], existing: dict[str, int]) -> str:
    author = _first_author(paper.get("authors") or paper.get("author"))
    year = paper.get("year") or "n.d."
    journal = _journal_short(paper.get("journal", ""))
    title_slug = _slugify(paper.get("title", ""), max_len=24)
    base = f"{author}{year}_{journal}_{title_slug}"
    base = re.sub(r"[^A-Za-z0-9_]+", "_", base)
    if base not in existing:
        existing[base] = 0
        return base
    existing[base] += 1
    suffix = chr(ord("a") + existing[base] - 1)
    return f"{base}_{suffix}"


def export_bibtex(
    run_id: str,
    source_runs_dir: Path = Path("logs/runs"),
    output_base_dir: Path = Path("data/runs"),
) -> str:
    run_dir = source_runs_dir / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    papers = _load_jsonl(run_dir / "papers.jsonl")
    output_dir = output_base_dir / run_id / "zotero"
    output_dir.mkdir(parents=True, exist_ok=True)

    keys: dict[str, int] = {}
    entries: list[str] = []
    for paper in papers:
        entry_key = safe_key(paper, keys)
        authors = paper.get("authors") or paper.get("author") or []
        if isinstance(authors, list):
            author_field = " and ".join(authors)
        else:
            author_field = str(authors)

        lines = [
            f"@article{{{entry_key},",
            "  title={" + str(paper.get("title", "Untitled")) + "}},",
            "  author={" + author_field + "}},",
        ]
        if paper.get("journal"):
            lines.append("  journal={" + str(paper.get("journal")) + "}},")
        if paper.get("year"):
            lines.append("  year={" + str(paper.get("year")) + "}},")
        if paper.get("doi"):
            lines.append("  doi={" + str(paper.get("doi")) + "}},")
        if paper.get("pmid"):
            lines.append("  pmid={" + str(paper.get("pmid")) + "}},")
        if paper.get("url"):
            lines.append("  url={" + str(paper.get("url")) + "}},")
        lines.append("}")
        entries.append("\n".join(lines))

    output_path = output_dir / "refs.bib"
    output_path.write_text("\n\n".join(entries), encoding="utf-8")
    return str(output_path)