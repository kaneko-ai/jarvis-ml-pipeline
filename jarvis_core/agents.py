# ============================================================
# jarvis_core/agents.py — BUG-1, BUG-2, BUG-3 修正版
# ============================================================
# 変更点:
#   BUG-1: _extract_query() を改善してキーワードだけを抽出
#          _detect_step() をデフォルト "collect" に変更
#   BUG-2: run_single() で Citation オブジェクトを生成して返す
#   BUG-3: run_single() で Gemini による日本語要約・エビデンスレベル追加
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
import re
import logging
from typing import Any
import types

from .llm import LLMClient, Message
from .sources.arxiv_client import ArxivClient, ArxivPaper
from .sources.crossref_client import CrossrefClient, CrossrefWork
from .sources.pubmed_client import PubMedArticle, PubMedClient

logger = logging.getLogger(__name__)

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
    """Paper search agent backed by free literature APIs.
    
    修正済み (BUG-1, BUG-2, BUG-3):
    - _extract_query(): ゴール全文ではなくキーワードのみ抽出
    - _detect_step(): デフォルトを "collect" に固定（サブタスクテキストに惑わされない）
    - run_single(): Citation オブジェクトを生成して返す (BUG-2)
    - run_single(): Gemini で日本語要約・エビデンスレベルを付与 (BUG-3)
    """

    name = "paper_fetcher"

    _CLARIFY_STEP = "Clarify paper requirements and search keywords"
    _COLLECT_STEP = "Collect candidate papers or sources"
    _SUMMARY_STEP = "Summarize findings against the goal"
    _DEFAULT_MAX_RESULTS = 5

    # --- BUG-1 修正: アクションワードを除去するための正規表現 ---
    _ACTION_WORDS = re.compile(
        r"(?i)^(search|find|fetch|collect|get|retrieve|look\s+up|summarize|"
        r"analyze|review|identify|list|show|give\s+me|探して|検索して|"
        r"要約して|まとめて|調べて|見つけて)\s+",
    )
    _QUANTITY_PREFIX = re.compile(
        r"(?i)^\d+\s+(recent\s+|latest\s+|new\s+)?(papers?|articles?|studies?|論文)\s+"
        r"(about|on|regarding|related\s+to|concerning|に関する|について)\s*",
    )

    def __init__(
        self,
        pubmed_client: PubMedClient | None = None,
        arxiv_client: ArxivClient | None = None,
        crossref_client: CrossrefClient | None = None,
    ) -> None:
        self.pubmed_client = pubmed_client or PubMedClient()
        self.arxiv_client = arxiv_client or ArxivClient()
        self.crossref_client = crossref_client or CrossrefClient()

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        """論文検索を実行し、Citation付きの結果を返す。
        
        BUG-1: _extract_query() でキーワードのみ抽出
        BUG-2: 各論文を Citation オブジェクトに変換
        BUG-3: LLM で日本語要約・エビデンスレベルを付与
        """
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

        # --- 常に collect として論文を検索（BUG-1 修正の核心） ---
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

        # --- BUG-3: Gemini で各論文に日本語要約とエビデンスレベルを付与 ---
        papers = self._enrich_papers_with_llm(llm, papers)

        # --- BUG-2: Citation オブジェクトを生成 ---
        citations = self._build_citations(papers)

        answer = self._build_answer(query=query, papers=papers)
        return AgentResult(
            status="success",
            answer=answer,
            citations=citations,
            meta={
                "source": "paper_fetcher",
                "query": query,
                "papers": papers,
                "paper_count": len(papers),
                "warnings": warnings,
                "sources": sorted({str(p.get("source", "")) for p in papers if p.get("source")}),
            },
        )

    def _detect_step(self, task: str) -> str:
        """ステップ検出（BUG-1 修正）。
        
        変更前: タスクテキストに _SUMMARY_STEP 等が含まれるかで判定
            → Plannerのサブタスクタイトルに "Summarize" が入ると誤判定
        
        変更後: "clarify" は明示的に指定された場合のみ。
                それ以外は常に "collect"（論文検索を実行）。
                summarize ステップでも論文データが必要なので collect で統一。
        """
        # clarify は最初のサブタスクでのみ発動。
        # ただし task テキストの先頭が明確に clarify 指示の場合のみ。
        first_line = next((line.strip() for line in task.splitlines() if line.strip()), "")
        if first_line == self._CLARIFY_STEP:
            return "clarify"
        # それ以外はすべて collect（論文検索実行）
        return "collect"

    def _extract_query(self, task: str) -> str:
        """タスクテキストから検索キーワードのみを抽出（BUG-1 修正の核心）。
        
        変更前: "Query:" 行があればその値を返し、なければ最初の行をそのまま返す
            → Planner/Router が加工したテキスト全体がクエリになってしまう
        
        変更後: 
          1. "Query:" 行があればその値を使う
          2. ゴールテキスト（最初の意味のある行）からアクションワードや
             ステップ説明を除去し、科学的トピックだけを抽出する
          3. 最終的に短いキーワードに整える
        """
        # Step 1: "Query:" 行を探す
        match = re.search(r"^Query:\s*(.+)$", task, flags=re.MULTILINE)
        if match:
            raw_query = match.group(1).strip()
            # Query: 行自体がゴール全文の場合があるので、さらにクリーニング
            return self._clean_query(raw_query)

        # Step 2: ゴールテキストを抽出（ステップ説明や装飾を除去）
        goal_text = self._extract_goal_from_task_text(task)
        return self._clean_query(goal_text)

    def _extract_goal_from_task_text(self, task: str) -> str:
        """タスクテキストからゴール部分だけを取り出す。
        
        Router._render_task_text() の出力形式:
          "{goal}\nQuery: {query}\nContext: {ctx}"
        
        Planner が作るサブタスクの title:
          "{goal[:50]}... — {step_description}"
        """
        lines = [line.strip() for line in task.splitlines() if line.strip()]
        if not lines:
            return ""

        # "Query:" や "Context:" 行を除外
        content_lines = []
        for line in lines:
            if re.match(r"^(Query|Context):\s*", line):
                continue
            content_lines.append(line)

        if not content_lines:
            # Query: 行しかなかった場合はそれを使う
            for line in lines:
                m = re.match(r"^Query:\s*(.+)$", line)
                if m:
                    return m.group(1).strip()
            return lines[0] if lines else ""

        # 最初の内容行を取得
        first_line = content_lines[0]

        # " — {step}" 部分を除去（Planner が付けるサブタスクタイトル）
        for step in (self._CLARIFY_STEP, self._COLLECT_STEP, self._SUMMARY_STEP):
            # "Goal text — Summarize findings against the goal" → "Goal text"
            sep_patterns = [f" — {step}", f" - {step}", f"— {step}", f"- {step}"]
            for sep in sep_patterns:
                if sep in first_line:
                    first_line = first_line.split(sep, 1)[0]
            # step が行の先頭にある場合も除去
            if first_line.strip().startswith(step):
                first_line = first_line.strip()[len(step):]

        return first_line.strip(" -:|.;,")

    def _clean_query(self, raw: str) -> str:
        """生のテキストから科学的キーワードのみを抽出する。
        
        "Search 5 recent papers about PD-1 and summarize" → "PD-1"
        "PD-1に関する最新の論文を10件検索して日本語で要約" → "PD-1"
        """
        text = raw.strip()
        if not text:
            return ""

        # ステップ説明文の除去（念のため）
        for step in (self._CLARIFY_STEP, self._COLLECT_STEP, self._SUMMARY_STEP):
            text = text.replace(step, "")

        # "and summarize" / "and analyze" 等の後続アクションを除去
        text = re.sub(
            r"(?i)\s+and\s+(summarize|analyze|review|compare|evaluate|list|rank|grade)\b.*$",
            "",
            text,
        )

        # 日本語のアクション部分を除去
        # "PD-1に関する最新の論文を10件検索して日本語で要約" → "PD-1"
        text = re.sub(
            r"(に関する|について|に対する|の|related\s+to)(最新の|recent\s+)?"
            r"(論文|文献|研究|papers?|articles?|studies?)"
            r"(を?\d+件?)?.*$",
            "",
            text,
        )

        # 英語のアクションワード除去: "Search 5 recent papers about PD-1"
        # まず "Search" 等のアクション動詞を除去
        text = self._ACTION_WORDS.sub("", text).strip()
        # "5 recent papers about" 等の数量+名詞+前置詞を除去
        text = self._QUANTITY_PREFIX.sub("", text).strip()

        # "about PD-1" → "PD-1" （前置詞が残っている場合）
        text = re.sub(
            r"(?i)^(about|on|regarding|concerning|for|of)\s+",
            "",
            text,
        ).strip()

        # 末尾の不要な接続詞や句読点を除去
        text = re.sub(r"[\s,;.。、]+$", "", text)
        text = re.sub(r"(?i)\s+(and|or)\s*$", "", text)

        # もし結果が空か非常に長い（50文字超 = クリーニング失敗）場合、
        # フォールバック: 大文字/ハイフン/数字を含む科学用語っぽいトークンを抽出
        if not text or len(text) > 50:
            tokens = self._extract_scientific_tokens(raw)
            if tokens:
                text = " ".join(tokens)

        return text.strip()

    def _extract_scientific_tokens(self, text: str) -> list[str]:
        """テキストから科学用語っぽいトークンを抽出するフォールバック。
        
        大文字+数字、ハイフン付き（PD-1, CRISPR-Cas9, IL-6 等）を優先的に取得。
        """
        # 科学用語パターン: PD-1, CRISPR, mTOR, IL-6, spermidine, etc.
        scientific_pattern = re.compile(
            r"\b([A-Z][A-Za-z]*-?\d+[A-Za-z]*"  # PD-1, IL-6, CD8
            r"|[A-Z]{2,}(?:-[A-Za-z0-9]+)*"       # CRISPR, CRISPR-Cas9, mRNA
            r"|[a-z]+[A-Z][a-zA-Z]*"               # spermidine-like camelCase
            r"|(?:spermidine|autophagy|immunotherapy|checkpoint|apoptosis))\b",  # 既知用語
            re.IGNORECASE,
        )
        matches = scientific_pattern.findall(text)
        # 重複除去しつつ順序を保持
        seen = set()
        result = []
        for m in matches:
            key = m.lower()
            if key not in seen and key not in {
                "search", "find", "collect", "summarize", "query",
                "papers", "paper", "about", "recent", "latest",
            }:
                seen.add(key)
                result.append(m)
        return result[:5]  # 最大5トークン

    def _extract_max_results(self, task: str) -> int:
        patterns = [
            r"(?i)\b(?:search|find|fetch|collect)\s+(\d+)\s+papers?\b",
            r"(?i)\b(\d+)\s+papers?\b",
            r"(?i)\btop\s+(\d+)\b",
            r"(\d+)\s*件",  # 日本語: "10件"
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

    # --- BUG-2: Citation オブジェクト生成 ---
    def _build_citations(self, papers: list[dict[str, Any]]) -> list[Citation]:
        """各論文から Citation オブジェクトを生成する。
        
        QualityGateVerifier が require_citations=True, require_locators=True で
        チェックするため、chunk_id, source, locator, quote すべて必要。
        """
        citations = []
        for paper in papers:
            source = str(paper.get("source", "unknown"))
            source_id = str(paper.get("source_id", ""))
            title = str(paper.get("title", "Untitled"))

            # chunk_id: ソースとIDの組み合わせ
            chunk_id = paper.get("paper_id", f"{source}:{source_id}")

            # locator: 論文の場所を特定する情報
            if source == "pubmed" and source_id:
                locator = f"pmid:{source_id}"
            elif source == "arxiv" and source_id:
                locator = f"arxiv:{source_id}"
            elif paper.get("doi"):
                locator = f"doi:{paper['doi']}"
            else:
                locator = f"url:{paper.get('url', 'unknown')}"

            # quote: 論文タイトル（要約があれば先頭100文字も追加）
            abstract = str(paper.get("abstract", ""))
            quote = title
            if abstract:
                quote = f"{title} — {abstract[:100]}..."

            citations.append(Citation(
                chunk_id=chunk_id,
                source=source,
                locator=locator,
                quote=quote,
            ))
        return citations

    # --- BUG-3: LLM で日本語要約・エビデンスレベルを付与 ---
    def _enrich_papers_with_llm(
        self, llm: LLMClient, papers: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """各論文に summary_ja と evidence_level を付与する。
        
        Gemini API レート制限 (Tier 1 = 15 RPM) を考慮し、
        1論文ずつ要約。失敗しても元の papers データは保持。
        """
        import time as _time
        import json as _json

        for paper in papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")

            if not abstract:
                paper["summary_ja"] = f"（アブストラクト未取得: {title}）"
                paper["evidence_level"] = "N/A"
                continue

            system_prompt = (
                "あなたは医学・生命科学の文献レビュー専門家です。\n"
                "以下の論文のアブストラクトを読んで、2つのことを行ってください:\n"
                "1. 日本語で3-5文の要約を作成\n"
                "2. CEBM (Centre for Evidence-Based Medicine) のエビデンスレベルを推定\n"
                "   レベル: 1a, 1b, 1c, 2a, 2b, 2c, 3a, 3b, 4, 5\n\n"
                "出力はJSON形式で:\n"
                '{"summary_ja": "...", "evidence_level": "..."}\n'
                "JSONのみ出力し、他のテキストは含めないでください。"
            )
            user_prompt = f"Title: {title}\n\nAbstract: {abstract}"

            try:
                raw = llm.chat(
                    [
                        Message(role="system", content=system_prompt),
                        Message(role="user", content=user_prompt),
                    ]
                )
                # JSONパース（コードブロックに包まれている場合も対処）
                raw_clean = raw.strip()
                if raw_clean.startswith("```"):
                    # ```json ... ``` を除去
                    raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_clean)
                    raw_clean = re.sub(r"\s*```$", "", raw_clean)

                parsed = _json.loads(raw_clean)
                paper["summary_ja"] = parsed.get("summary_ja", "（要約生成失敗）")
                paper["evidence_level"] = parsed.get("evidence_level", "N/A")
            except Exception as e:
                logger.warning(f"LLM enrichment failed for '{title[:40]}': {e}")
                paper["summary_ja"] = f"（要約生成失敗: {e}）"
                paper["evidence_level"] = "N/A"

            # レート制限対策: 4秒待機（15 RPM = 4秒/リクエスト）
            _time.sleep(4)

        return papers

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
            summary_ja = paper.get("summary_ja", "")
            evidence_level = paper.get("evidence_level", "")

            line = f"{index}. {paper.get('title', 'Untitled')} ({year}; {venue}; {source})"
            if evidence_level and evidence_level != "N/A":
                line += f" [CEBM: {evidence_level}]"
            lines.append(line)
            if summary_ja:
                lines.append(f"   要約: {summary_ja}")
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
