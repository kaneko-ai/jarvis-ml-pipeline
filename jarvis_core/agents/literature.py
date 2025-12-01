from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from jarvis_core.task import Task, TaskCategory

from ..integrations.pubmed_client import fetch_pubmed_details, search_pubmed
from . import AgentResult

logger = logging.getLogger("jarvis_core.agents.literature")


@dataclass
class PaperSummary:
    pmid: str
    title: str
    journal: str
    year: int | None
    doi: str | None
    url: str | None
    abstract: str | None
    score: float = 0.0


class LiteratureSurveyAgent:
    """Agent that performs a lightweight literature search via PubMed."""

    name = "literature_survey"

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def run_task(self, task: Task) -> AgentResult:
        return run_literature_survey(task, config=self.config)

    def run_single(self, llm, task_text: str) -> AgentResult:  # noqa: ANN001, D401
        """Fallback to run_task using the provided text as goal."""

        faux_task = Task(
            id="ad-hoc-literature-task",
            category=TaskCategory.LITERATURE_REVIEW,
            goal=task_text,
            inputs={},
            constraints={},
        )
        return self.run_task(faux_task)


def _format_markdown(papers: List[PaperSummary], query: str) -> str:
    lines = [f"# Literature Survey for `{query}`", ""]
    for paper in papers:
        title = paper.title or "(no title)"
        journal = paper.journal or "N/A"
        year = paper.year if paper.year is not None else "N/A"
        doi = f" DOI: {paper.doi}" if paper.doi else ""
        pmid = paper.pmid or "N/A"
        lines.append(f"- **{title}** ({journal}, {year}){doi} PMID: {pmid}")
        if paper.url:
            lines.append(f"  - {paper.url}")
        if paper.abstract:
            abstract = paper.abstract
            if len(abstract) > 240:
                abstract = abstract[:240] + "..."
            lines.append(f"  - Abstract: {abstract}")
        lines.append("")
    return "\n".join(lines).strip()


def run_literature_survey(task: Task, config: Dict[str, Any] | None = None) -> AgentResult:
    """Run a literature survey using PubMed and return a markdown summary."""

    cfg = config or {}
    inputs = task.inputs or {}
    query = inputs.get("query") or task.goal
    max_results = int(inputs.get("max_results") or cfg.get("default_max_results", 20))

    pmids = search_pubmed(query, max_results=max_results)
    papers = fetch_pubmed_details(pmids)

    for paper in papers:
        paper.score = float(paper.year or 0)
    papers.sort(key=lambda p: p.score, reverse=True)

    top_papers = papers[:max_results]
    answer = _format_markdown(top_papers, query)
    meta = {"papers": [paper.__dict__ for paper in top_papers]}
    thought = f"Collected {len(top_papers)} papers for query '{query}'."
    logger.info("Literature survey completed for query '%s' with %d papers", query, len(top_papers))
    return AgentResult(thought=thought, answer=answer, score=float(len(top_papers)), meta=meta)
