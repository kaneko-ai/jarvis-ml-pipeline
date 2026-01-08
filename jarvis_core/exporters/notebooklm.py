"""NotebookLM Exporter.

Per RP-171, exports papers for NotebookLM learning flow.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class NotebookLMExport:
    """Export for NotebookLM."""

    title: str
    chapters: list[dict]
    summary: str
    review_questions: list[str]


def export_for_notebooklm(
    paper_data: dict,
    output_path: str | None = None,
) -> str:
    """Export paper data for NotebookLM.

    Structure:
    1. Graphical Abstract (if available)
    2. Figures & Tables
    3. Abstract
    4. Discussion
    5. Introduction
    6. Methods
    7. Review Summary

    Args:
        paper_data: Paper data with sections.
        output_path: Optional output file path.

    Returns:
        Markdown content.
    """
    sections = []

    title = paper_data.get("title", "Research Paper")
    sections.append(f"# {title}\n")

    # Graphical Abstract
    if paper_data.get("graphical_abstract"):
        sections.append("## Graphical Abstract\n")
        sections.append(paper_data["graphical_abstract"] + "\n")

    # Figures & Tables (high priority for learning)
    figures = paper_data.get("figures", [])
    if figures:
        sections.append("## Key Figures & Tables\n")
        for fig in figures:
            sections.append(f"### {fig.get('id', 'Figure')}\n")
            sections.append(fig.get("caption", "") + "\n")

    # Abstract
    if paper_data.get("abstract"):
        sections.append("## Abstract\n")
        sections.append(paper_data["abstract"] + "\n")

    # Discussion (key findings)
    if paper_data.get("discussion"):
        sections.append("## Key Discussion Points\n")
        sections.append(paper_data["discussion"][:2000] + "\n")

    # Introduction (background)
    if paper_data.get("introduction"):
        sections.append("## Background\n")
        sections.append(paper_data["introduction"][:1500] + "\n")

    # Methods (brief)
    if paper_data.get("methods"):
        sections.append("## Methods Summary\n")
        sections.append(paper_data["methods"][:1000] + "\n")

    # Review Summary
    sections.append("## Review Summary\n")
    sections.append(_generate_review_summary(paper_data) + "\n")

    # Review Questions
    sections.append("## Self-Test Questions\n")
    questions = _generate_review_questions(paper_data)
    for i, q in enumerate(questions, 1):
        sections.append(f"{i}. {q}\n")

    content = "\n".join(sections)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")

    return content


def _generate_review_summary(paper_data: dict) -> str:
    """Generate a brief review summary."""
    points = []

    if paper_data.get("main_findings"):
        points.append(f"**Main Findings:** {paper_data['main_findings']}")

    if paper_data.get("claims"):
        claims = paper_data["claims"][:3]
        points.append("**Key Claims:**")
        for claim in claims:
            text = claim.get("text", str(claim))[:100]
            points.append(f"- {text}")

    if not points:
        points.append("Review the abstract and discussion for key takeaways.")

    return "\n".join(points)


def _generate_review_questions(paper_data: dict) -> list[str]:
    """Generate review questions from paper content."""
    questions = []

    if paper_data.get("title"):
        questions.append(f"What is the main research question addressed in '{paper_data['title'][:50]}'?")

    if paper_data.get("methods"):
        questions.append("What methodology was used in this study?")

    if paper_data.get("claims"):
        questions.append("What are the key findings of this research?")

    questions.append("What are the limitations of this study?")
    questions.append("How could this research be applied in practice?")

    return questions[:5]


def export_batch_for_notebooklm(
    papers: list[dict],
    output_dir: str,
) -> list[str]:
    """Export multiple papers for NotebookLM.

    Args:
        papers: List of paper data dicts.
        output_dir: Output directory.

    Returns:
        List of output file paths.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    paths = []
    for i, paper in enumerate(papers):
        title = paper.get("title", f"paper_{i}")
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:50]
        filepath = output_path / f"{safe_title}.md"
        export_for_notebooklm(paper, str(filepath))
        paths.append(str(filepath))

    return paths
