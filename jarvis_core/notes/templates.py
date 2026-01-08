"""Templates for Obsidian research notes."""
from __future__ import annotations

from datetime import datetime, timezone

TEMPLATE_VERSION = "p4-obsidian-1.0"


def format_frontmatter(
    *,
    paper_id: str,
    title: str,
    year: int | None,
    journal: str | None,
    doi: str | None,
    pmid: str | None,
    pmcid: str | None,
    oa_status: str,
    tier: str,
    score: float,
    tags: list[str],
    source_run: str,
    created_at: str | None = None,
) -> str:
    """Format YAML frontmatter for a paper note."""
    created = created_at or datetime.now(timezone.utc).isoformat()
    tags_yaml = "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    journal_value = journal or ""
    def _yaml_value(value: str | None) -> str:
        if value is None or value == "":
            return "null"
        return f"\"{value}\""

    doi_value = _yaml_value(doi)
    pmid_value = _yaml_value(pmid)
    pmcid_value = _yaml_value(pmcid)
    return "\n".join(
        [
            "---",
            f"paper_id: \"{paper_id}\"",
            f"title: \"{title}\"",
            f"year: {year if year is not None else 'null'}",
            f"journal: \"{journal_value}\"",
            f"doi: {doi_value}",
            f"pmid: {pmid_value}",
            f"pmcid: {pmcid_value}",
            f"oa_status: \"{oa_status}\"",
            f"tier: \"{tier}\"",
            f"score: {score:.2f}",
            f"tags: {tags_yaml}",
            f"source_run: \"{source_run}\"",
            f"created_at: \"{created}\"",
            "---",
            "",
        ]
    )


def format_section(title: str, body: str) -> str:
    """Format a markdown section."""
    return f"## {title}\n\n{body.strip()}\n"


def format_bullet_list(items: list[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def format_run_overview_header(run_id: str, query: str, filters: str) -> str:
    return "\n".join(
        [
            f"# Run Overview: {run_id}",
            "",
            f"**Query**: {query}",
            f"**Filters**: {filters}",
            "",
        ]
    )
