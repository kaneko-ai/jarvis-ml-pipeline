from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .llm import LLMClient, Message


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
        except Exception:
            return AgentResult(
                status="fail",
                answer="",
                citations=[],
                meta={"warnings": ["llm_error"]},
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
        except Exception:
            return AgentResult(
                status="fail",
                answer="",
                citations=[],
                meta={"warnings": ["llm_error"]},
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
        except Exception:
            return AgentResult(
                status="fail",
                answer="",
                citations=[],
                meta={"warnings": ["llm_error"]},
            )


class PaperFetcherAgent(BaseAgent):
    """Stub for paper-fetcher style agent."""

    name = "paper_fetcher"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:  # noqa: ARG002
        return AgentResult(
            status="success",
            answer=f"Stub: fetching papers for '{task}'",
            citations=[],
            meta={"source": "paper_fetcher_stub"},
        )


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
