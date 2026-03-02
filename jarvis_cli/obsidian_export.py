"""jarvis obsidian_export - Write papers to Obsidian Vault as Markdown (v2 T2-2 + B-5).

Each paper is saved as a .md file with YAML frontmatter in the Obsidian Vault.
Obsidian automatically detects new files via folder watching.

B-5 enhancements:
  - study_type and keywords in frontmatter
  - Evidence level badge (emoji-based)
  - Cross-references between papers from the same pipeline run
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import yaml


# B-5: Evidence level badge mapping
_EVIDENCE_BADGES = {
    "1a": "1a - Systematic Review of RCTs",
    "1b": "1b - Individual RCT",
    "1c": "1c - All or None",
    "2a": "2a - Systematic Review of Cohort",
    "2b": "2b - Individual Cohort / Low-quality RCT",
    "2c": "2c - Outcomes Research",
    "3a": "3a - Systematic Review of Case-Control",
    "3b": "3b - Individual Case-Control",
    "4":  "4 - Case Series",
    "5":  "5 - Expert Opinion / Basic Research",
}


def load_config(config_path: str = "config.yaml") -> dict:
    """Load config.yaml and return as dict."""
    p = Path(config_path)
    if not p.exists():
        return {
            "obsidian": {
                "vault_path": "",
                "papers_folder": "JARVIS/Papers",
                "notes_folder": "JARVIS/Notes",
            }
        }
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _safe_filename(title: str) -> str:
    """Convert a paper title to a safe filename."""
    safe = re.sub(r'[<>:"/\\|?*]', "", title)
    safe = safe.strip()
    safe = safe[:80]
    return safe if safe else "Untitled"


def export_single_paper(
    paper: dict,
    vault_path: str,
    papers_folder: str,
    sibling_titles: list[str] | None = None,
) -> Path:
    """Export one paper as a YAML frontmatter Markdown file to Obsidian Vault.

    Args:
        paper: Paper data dictionary
        vault_path: Obsidian Vault root folder path
        papers_folder: Subfolder within Vault for papers
        sibling_titles: Titles of other papers in same pipeline run (B-5 cross-ref)

    Returns:
        Path to the saved .md file
    """
    title = paper.get("title", "Untitled")
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    journal = paper.get("journal", paper.get("venue", ""))
    doi = paper.get("doi", "")
    pmid = paper.get("pmid", "")
    citation_count = paper.get("citation_count", 0)
    evidence_level = paper.get("evidence_level", "unknown")
    evidence_confidence = paper.get("evidence_confidence", 0.0)
    study_type = paper.get("study_type", "")
    summary_ja = paper.get("summary_ja", "")
    abstract = paper.get("abstract", "")
    source = paper.get("source", "")
    keywords = paper.get("keywords", [])

    # --- Build YAML frontmatter (B-5 enhanced) ---
    frontmatter = {
        "title": title,
        "authors": authors[:5],
        "year": year,
        "journal": journal,
        "doi": doi,
        "pmid": pmid,
        "citation_count": citation_count,
        "evidence_level": evidence_level,
        "evidence_confidence": evidence_confidence,
        "study_type": study_type,
        "keywords": keywords[:10] if keywords else [],
        "tags": ["JARVIS", f"evidence-{evidence_level}"],
        "source": "JARVIS Research OS",
        "created": date.today().isoformat(),
    }

    fm_str = yaml.dump(
        frontmatter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).strip()

    # --- Build Markdown body ---
    lines = []
    lines.append("---")
    lines.append(fm_str)
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")

    # B-5: Evidence badge
    badge_desc = _EVIDENCE_BADGES.get(evidence_level, evidence_level)
    if evidence_level and evidence_level != "unknown":
        lines.append(f"> **Evidence Level**: {badge_desc}")
        lines.append(f"> **Confidence**: {evidence_confidence:.0%}")
        if study_type and study_type != "unknown":
            display_type = study_type.replace("_", " ").title()
            lines.append(f"> **Study Type**: {display_type}")
        lines.append("")

    # Basic info section
    lines.append("## Basic Info")
    author_str = ", ".join(authors[:5])
    if len(authors) > 5:
        author_str += " et al."
    lines.append(f"- **Authors**: {author_str}")
    lines.append(f"- **Journal**: {journal} ({year})")
    lines.append(f"- **Source**: {source}")
    if citation_count:
        lines.append(f"- **Citations**: {citation_count:,}")
    if keywords:
        kw_str = ", ".join(keywords[:10])
        lines.append(f"- **Keywords**: {kw_str}")
    lines.append("")

    # Japanese summary (if available)
    if summary_ja:
        lines.append("## Japanese Summary")
        lines.append("")
        lines.append(summary_ja)
        lines.append("")

    # Abstract
    if abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(abstract)
        lines.append("")

    # Links
    lines.append("## Links")
    if pmid:
        lines.append(f"- [PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
    if doi:
        lines.append(f"- [DOI](https://doi.org/{doi})")
    lines.append("")

    # B-5: Cross-references to sibling papers
    if sibling_titles:
        other_titles = [t for t in sibling_titles if t != title]
        if other_titles:
            lines.append("## Related Papers (Same Search)")
            lines.append("")
            for t in other_titles:
                safe_t = _safe_filename(t)
                lines.append(f"- [[{safe_t}]]")
            lines.append("")

    # --- Write file ---
    output_dir = Path(vault_path) / papers_folder
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = _safe_filename(title) + ".md"
    output_path = output_dir / filename
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return output_path


def export_papers_to_obsidian(papers: list[dict], config: dict | None = None) -> list[Path]:
    """Export multiple papers to Obsidian Vault.

    Args:
        papers: List of paper data dictionaries
        config: Configuration dict (loaded from config.yaml if None)

    Returns:
        List of saved .md file paths
    """
    if config is None:
        config = load_config()

    obsidian_config = config.get("obsidian", {})
    vault_path = obsidian_config.get("vault_path", "")
    papers_folder = obsidian_config.get("papers_folder", "JARVIS/Papers")

    if not vault_path:
        raise ValueError(
            "Obsidian vault_path is not configured.\n"
            "Please set obsidian.vault_path in config.yaml.\n"
            'Example: vault_path: "C:\\\\Users\\\\kaneko yu\\\\Documents\\\\ObsidianVault"'
        )

    vault = Path(vault_path)
    if not vault.exists():
        print(f"  Note: Vault folder does not exist, creating: {vault_path}")
        vault.mkdir(parents=True, exist_ok=True)

    # B-5: Collect all titles for cross-referencing
    all_titles = [p.get("title", "Untitled") for p in papers]

    saved_paths = []
    for paper in papers:
        try:
            path = export_single_paper(paper, vault_path, papers_folder, sibling_titles=all_titles)
            saved_paths.append(path)
        except Exception as e:
            title = paper.get("title", "?")[:50]
            print(f"  Warning: Failed to export '{title}': {e}")

    return saved_paths
