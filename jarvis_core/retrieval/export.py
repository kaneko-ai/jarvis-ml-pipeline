"""Export utilities for retrieval results."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable

from jarvis_core.retrieval.schema import SearchResult


def export_json(results: Iterable[SearchResult]) -> str:
    payload = [result.to_dict() for result in results]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_markdown(results: Iterable[SearchResult]) -> str:
    lines = ["# Retrieval Results", ""]
    for result in results:
        chunk = result.chunk
        lines.append(f"## {chunk.title}")
        lines.append(f"- Score: {result.score:.4f}")
        lines.append(f"- Source: {chunk.source_type}")
        lines.append(f"- Doc ID: {chunk.doc_id}")
        lines.append(f"- Locator: {chunk.provenance.locator}")
        lines.append("")
        lines.append(result.snippet)
        lines.append("")
    return "\n".join(lines)


def export_csv(results: Iterable[SearchResult]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "doc_id",
            "chunk_id",
            "title",
            "score",
            "snippet",
            "run_id",
            "pmid",
            "section",
            "locator",
            "year",
            "tier",
            "oa",
        ],
    )
    writer.writeheader()
    for result in results:
        chunk = result.chunk
        writer.writerow(
            {
                "doc_id": chunk.doc_id,
                "chunk_id": chunk.chunk_id,
                "title": chunk.title,
                "score": f"{result.score:.6f}",
                "snippet": result.snippet,
                "run_id": chunk.provenance.run_id,
                "pmid": chunk.provenance.pmid,
                "section": chunk.provenance.section,
                "locator": chunk.provenance.locator,
                "year": chunk.meta.year,
                "tier": chunk.meta.tier,
                "oa": chunk.meta.oa,
            }
        )
    return output.getvalue()
