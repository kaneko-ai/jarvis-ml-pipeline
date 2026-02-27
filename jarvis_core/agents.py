from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any
import types

from .llm import LLMClient, Message
from .sources.arxiv_client import ArxivClient, ArxivPaper
from .sources.crossref_client import CrossrefClient, CrossrefWork
from .sources.pubmed_client import PubMedArticle, PubMedClient

base = types.ModuleType("jarvis_core.agents.base")
scientist = types.ModuleType("jarvis_core.agents.scientist")
registry = types.ModuleType("jarvis_core.agents.registry")


@dataclass
class Citation:
    """Citation reference per JARVIS_MASTER.md Section 5.4."""

    chunk_id: str
    source: str
    locator: str  # "page:3" | "pmid:..." | "url:..."
    quote: str


@dataclass
class AgentResult:
    """Agent output per JARVIS_MASTER.md Section 5.4.

    Note: thought field is explicitly prohibited by spec.
    """

    status: str  # "success" | "fail" | "partial"
    answer: str
    citations: list[Citation] = field(default_factory=list)
    meta: dict[str, Any] | None = None


class BaseAgent:
    """
    すべてのエージェントの共通ベースクラス。
    - run_single: 個別タスクを1案だけ生成
    - run_sampling: Verbalized Sampling を使って複数案を生成
    """

    name: str = "base"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        raise NotImplementedError

    def _create_result(self, answer: str, status: str = "success") -> AgentResult:
        """Create AgentResult with auto-extracted citations."""
        citations = self._extract_citations(answer)
        return AgentResult(status=status, answer=answer, citations=citations)

    def run_sampling(self, llm: LLMClient, task: str, n_candidates: int) -> list[AgentResult]:
        """
        Verbalized Sampling:
        - n_candidates 個の案をJSON形式で生成させる
        - 失敗した場合は run_single にフォールバック
        """
        import json

        system_prompt = (
            "あなたは高度なアシスタントです。"
            "以下のタスクに対して、複数の候補案を作成し、"
            "各候補について ANSWER を日本語で出力してください。"
            "出力は厳密なJSON配列とし、各要素は "
            '{"answer":...} の形式にしてください。'
        )
        user_prompt = f"タスク: {task}\n候補数: {n_candidates}"

        try:
            raw = llm.chat(
                [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=user_prompt),
                ]
            )
        except Exception:
            single = self.run_single(llm, task)
            return [single]

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            single = self.run_single(llm, task)
            return [single]

        results: list[AgentResult] = []
        for item in parsed[:n_candidates]:
            answer = self._extract_answer(item.get("answer", ""))
            if answer:
                results.append(AgentResult(status="success", answer=answer, citations=[]))
            else:
                results.append(
                    AgentResult(
                        status="fail",
                        answer="",
                        citations=[],
                        meta={"warnings": ["empty_answer"]},
                    )
                )
        if not results:
            results.append(self.run_single(llm, task))
        return results

    @staticmethod
    def _extract_answer(text: str) -> str:
        """Extract answer from LLM output."""
        if text is None:
            return ""
        return str(text).strip()

    @staticmethod
    def _extract_citations(text: str) -> list[Citation]:
        """Extract [chunk:ID] citations from text."""
        import re

        citations = []
        # Find all occurrences of [chunk:XXX]
        for match in re.finditer(r"\[chunk:([\w\-]+)\]", text):
            chunk_id = match.group(1)
            citations.append(Citation(chunk_id=chunk_id, source="", locator="", quote=""))
        return citations


class ThesisAgent(BaseAgent):
    name = "thesis"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        system_prompt = (
            "あなたは修士論文執筆支援の専門アシスタントです。"
            "生命科学・抗体関連の背景・考察を、専門性を保ちつつ、"
            "日本語N1レベルで簡潔かつ論理的に書き直してください。"
            "修論にそのまま貼れる形の本文を出力してください。"
        )
        try:
            raw = llm.chat(
                [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=task),
                ]
            )
            answer = self._extract_answer(raw)
            if not answer:
                return AgentResult(
                    status="fail",
                    answer="",
                    citations=[],
                    meta={"warnings": ["empty_answer"]},
                )
            return self._create_result(answer)
        except Exception as e:
            return AgentResult(
                status="fail",
                answer="",
                citations=[],
                meta={"warnings": [f"llm_error: {e}"]},
            )


class ESEditAgent(BaseAgent):
    name = "es_edit"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        system_prompt = (
            "あなたは製薬業界就活のエントリーシート添削アシスタントです。"
            "文系人事にも伝わるように専門用語を噛み砕き、"
            "独自性と論理性を両立した文章に整えてください。"
            "ESにそのまま貼れる文章を出力してください。"
        )
        try:
            raw = llm.chat(
                [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=task),
                ]
            )
            answer = self._extract_answer(raw)
            if not answer:
                return AgentResult(
                    status="fail",
                    answer="",
                    citations=[],
                    meta={"warnings": ["empty_answer"]},
                )
            return self._create_result(answer)
        except Exception as e:
            return AgentResult(
                status="fail",
                answer="",
                citations=[],
                meta={"warnings": [f"llm_error: {e}"]},
            )


class MiscAgent(BaseAgent):
    name = "misc"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        system_prompt = (
            "あなたは一般的な質問に答える汎用アシスタントです。"
            "日本語N1レベルで簡潔かつ正確に回答してください。"
        )
        try:
            raw = llm.chat(
                [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=task),
                ]
            )
            answer = self._extract_answer(raw)
            if not answer:
                return AgentResult(
                    status="fail",
                    answer="",
                    citations=[],
                    meta={"warnings": ["empty_answer"]},
                )
            return self._create_result(answer)
        except Exception as e:
            return AgentResult(
                status="fail",
                answer="",
                citations=[],
                meta={"warnings": [f"llm_error: {e}"]},
            )


class PaperFetcherAgent(BaseAgent):
    """Paper search agent backed by free literature APIs."""

    name = "paper_fetcher"

    _CLARIFY_STEP = "Clarify paper requirements and search keywords"
    _COLLECT_STEP = "Collect candidate papers or sources"
    _SUMMARY_STEP = "Summarize findings against the goal"
    _DEFAULT_MAX_RESULTS = 5

    def __init__(
        self,
        pubmed_client: PubMedClient | None = None,
        arxiv_client: ArxivClient | None = None,
        crossref_client: CrossrefClient | None = None,
    ) -> None:
        self.pubmed_client = pubmed_client or PubMedClient()
        self.arxiv_client = arxiv_client or ArxivClient()
        self.crossref_client = crossref_client or CrossrefClient()

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:  # noqa: ARG002
        query = self._extract_query(task)
        max_results = self._extract_max_results(task)
        step = self._detect_step(task)

        if not query:
            return AgentResult(
                status="fail",
                answer="",
                citations=[],
                meta={
                    "source": "paper_fetcher",
                    "papers": [],
                    "warnings": ["empty_query"],
                },
            )

        if step == "clarify":
            return AgentResult(
                status="success",
                answer=(
                    f"Search plan for '{query}': query PubMed first, then fall back to arXiv "
                    f"and Crossref if needed. Target {max_results} papers."
                ),
                citations=[],
                meta={
                    "source": "paper_fetcher",
                    "query": query,
                    "papers": [],
                    "paper_count": 0,
                },
            )

        papers, warnings = self._search_papers(query=query, max_results=max_results)
        if not papers:
            warnings.append("no_papers_found")
            return AgentResult(
                status="partial",
                answer=f"No papers found for '{query}'.",
                citations=[],
                meta={
                    "source": "paper_fetcher",
                    "query": query,
                    "papers": [],
                    "paper_count": 0,
                    "warnings": warnings,
                },
            )

        answer = self._build_answer(query=query, papers=papers)
        return AgentResult(
            status="success",
            answer=answer,
            citations=[],
            meta={
                "source": "paper_fetcher",
                "query": query,
                "papers": [] if step == "summarize" else papers,
                "paper_count": len(papers),
                "warnings": warnings,
                "sources": sorted({str(p.get("source", "")) for p in papers if p.get("source")}),
            },
        )

    def _detect_step(self, task: str) -> str:
        if self._CLARIFY_STEP in task:
            return "clarify"
        if self._SUMMARY_STEP in task:
            return "summarize"
        return "collect"

    def _extract_query(self, task: str) -> str:
        match = re.search(r"^Query:\s*(.+)$", task, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()

        first_line = next((line.strip() for line in task.splitlines() if line.strip()), "")
        for step in (self._CLARIFY_STEP, self._COLLECT_STEP, self._SUMMARY_STEP):
            if step in first_line:
                first_line = first_line.split(step, 1)[0]
        return first_line.strip(" -:|.;,")

    def _extract_max_results(self, task: str) -> int:
        patterns = [
            r"(?i)\b(?:search|find|fetch|collect)\s+(\d+)\s+papers?\b",
            r"(?i)\b(\d+)\s+papers?\b",
            r"(?i)\btop\s+(\d+)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, task)
            if match:
                value = int(match.group(1))
                return max(1, min(value, 20))
        return self._DEFAULT_MAX_RESULTS

    def _search_papers(self, query: str, max_results: int) -> tuple[list[dict[str, Any]], list[str]]:
        papers: list[dict[str, Any]] = []
        warnings: list[str] = []
        seen: set[str] = set()

        def extend_with(items: list[dict[str, Any]]) -> None:
            for item in items:
                key = self._paper_key(item)
                if key in seen:
                    continue
                seen.add(key)
                papers.append(item)
                if len(papers) >= max_results:
                    break

        try:
            pubmed_articles = self.pubmed_client.search_and_fetch(query, max_results=max_results)
            extend_with([self._normalize_pubmed_article(article) for article in pubmed_articles])
        except Exception as exc:
            warnings.append(f"pubmed_error:{exc}")

        if len(papers) < max_results:
            try:
                remaining = max_results - len(papers)
                arxiv_papers = self.arxiv_client.search(query, max_results=remaining)
                extend_with([self._normalize_arxiv_paper(paper) for paper in arxiv_papers])
            except Exception as exc:
                warnings.append(f"arxiv_error:{exc}")

        if len(papers) < max_results:
            try:
                remaining = max_results - len(papers)
                crossref_works = self.crossref_client.search(
                    query,
                    rows=remaining,
                    filter_type="journal-article",
                )
                extend_with([self._normalize_crossref_work(work) for work in crossref_works])
            except Exception as exc:
                warnings.append(f"crossref_error:{exc}")

        return papers[:max_results], warnings

    def _normalize_pubmed_article(self, article: PubMedArticle) -> dict[str, Any]:
        title = article.title.strip() or "Untitled"
        return {
            "paper_id": f"pubmed:{article.pmid or self._slugify(title)}",
            "source": "pubmed",
            "source_id": article.pmid,
            "title": title,
            "year": self._extract_year(article.pub_date),
            "authors": article.authors,
            "abstract": article.abstract,
            "journal": article.journal,
            "pub_date": article.pub_date,
            "doi": article.doi,
            "pmid": article.pmid,
            "pmc_id": article.pmc_id,
            "keywords": article.keywords,
            "mesh_terms": article.mesh_terms,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/" if article.pmid else "",
        }

    def _normalize_arxiv_paper(self, paper: ArxivPaper) -> dict[str, Any]:
        title = paper.title.strip() or "Untitled"
        year = paper.published.year if paper.published else (paper.updated.year if paper.updated else 0)
        return {
            "paper_id": f"arxiv:{paper.arxiv_id or self._slugify(title)}",
            "source": "arxiv",
            "source_id": paper.arxiv_id,
            "title": title,
            "year": year,
            "authors": paper.authors,
            "abstract": paper.abstract,
            "journal": paper.journal_ref or "",
            "doi": paper.doi,
            "arxiv_id": paper.arxiv_id,
            "categories": paper.categories,
            "primary_category": paper.primary_category,
            "published": paper.published.isoformat() if paper.published else None,
            "updated": paper.updated.isoformat() if paper.updated else None,
            "url": paper.abs_url or paper.pdf_url or "",
            "pdf_url": paper.pdf_url,
        }

    def _normalize_crossref_work(self, work: CrossrefWork) -> dict[str, Any]:
        title = work.title.strip() or "Untitled"
        year = work.published_date.year if work.published_date else 0
        return {
            "paper_id": f"doi:{work.doi.lower()}" if work.doi else f"crossref:{self._slugify(title)}",
            "source": "crossref",
            "source_id": work.doi,
            "title": title,
            "year": year,
            "authors": work.authors,
            "abstract": work.abstract or "",
            "journal": work.journal or "",
            "doi": work.doi,
            "publisher": work.publisher,
            "type": work.type,
            "citation_count": work.cited_by_count,
            "references_count": work.references_count,
            "url": work.url or (f"https://doi.org/{work.doi}" if work.doi else ""),
        }

    def _paper_key(self, paper: dict[str, Any]) -> str:
        doi = str(paper.get("doi") or "").strip().lower()
        if doi:
            return f"doi:{doi}"
        source = str(paper.get("source") or "").strip().lower()
        source_id = str(paper.get("source_id") or "").strip().lower()
        if source and source_id:
            return f"{source}:{source_id}"
        title = str(paper.get("title") or "").strip().lower()
        return f"title:{self._slugify(title)}"

    def _build_answer(self, query: str, papers: list[dict[str, Any]]) -> str:
        lines = [f"Found {len(papers)} papers for '{query}'."]
        for index, paper in enumerate(papers, start=1):
            year = paper.get("year") or "n.d."
            venue = paper.get("journal") or paper.get("source") or "unknown venue"
            source = paper.get("source") or "unknown"
            lines.append(f"{index}. {paper.get('title', 'Untitled')} ({year}; {venue}; {source})")
        return "\n".join(lines)

    def _extract_year(self, pub_date: str) -> int:
        match = re.search(r"\b(19|20)\d{2}\b", pub_date or "")
        return int(match.group()) if match else 0

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "untitled"


class MyGPTPaperAnalyzerAgent(BaseAgent):
    """Stub for mygpt-paper-analyzer integration."""

    name = "mygpt_paper_analyzer"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:  # noqa: ARG002
        return AgentResult(
            status="success",
            answer=f"Stub: analyzing papers for '{task}'",
            citations=[],
            meta={"source": "mygpt_paper_analyzer_stub"},
        )


class JobAssistantAgent(BaseAgent):
    """Stub for job-hunting assistant (ES, interview prep)."""

    name = "job_assistant"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:  # noqa: ARG002
        return AgentResult(
            status="success",
            answer=f"Stub: job assistance for '{task}'",
            citations=[],
            meta={"source": "job_assistant_stub"},
        )
