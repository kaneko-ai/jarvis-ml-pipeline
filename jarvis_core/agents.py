from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

from .llm import LLMClient, Message


@dataclass
class AgentResult:
    thought: str
    answer: str
    score: float = 0.0
    meta: Dict[str, Any] | None = None


class BaseAgent:
    """
    すべてのエージェントの共通ベースクラス。
    - run_single: 個別タスクを1案だけ生成
    - run_sampling: Verbalized Sampling を使って複数案を生成
    """

    name: str = "base"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        raise NotImplementedError

    def run_sampling(
        self, llm: LLMClient, task: str, n_candidates: int
    ) -> List[AgentResult]:
        """
        Verbalized Sampling:
        - n_candidates 個の案をJSON形式で生成させる
        - 失敗した場合は run_single にフォールバック
        """
        import json

        system_prompt = (
            "あなたは高度なアシスタントです。"
            "以下のタスクに対して、複数の候補案を作成し、"
            "各候補について THOUGHT, ANSWER, SCORE を日本語で出力してください。"
            "出力は厳密なJSON配列とし、各要素は "
            '{"thought":..., "answer":..., "score":...} の形式にしてください。'
            "scoreは0〜1の実数で、自分で考える完成度を表してください。"
        )
        user_prompt = f"タスク: {task}\n候補数: {n_candidates}"

        raw = llm.chat(
            [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ]
        )

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # JSONになっていなければ単一案にフォールバック
            single = self.run_single(llm, task)
            return [single]

        results: List[AgentResult] = []
        for item in parsed[:n_candidates]:
            results.append(
                AgentResult(
                    thought=item.get("thought", ""),
                    answer=item.get("answer", ""),
                    score=float(item.get("score", 0.0)),
                    meta={"raw": item},
                )
            )
        if not results:
            results.append(self.run_single(llm, task))
        return results

    @staticmethod
    def _parse_yaml_like(text: str) -> tuple[str, str]:
        """
        thought: |-
          ...
        answer: |-
          ...
        という簡易YAMLライクな出力から thought / answer を抜き出す。
        """
        thought = ""
        answer = ""
        current: str | None = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("thought:"):
                current = "thought"
                continue
            if stripped.startswith("answer:"):
                current = "answer"
                continue
            if current == "thought":
                thought += line + "\n"
            elif current == "answer":
                answer += line + "\n"

        # もし thought/answer がどちらも空なら、
        # LLMの出力全体をそのまま answer として扱う
        if not thought.strip() and not answer.strip():
            return "", text.strip()

        return thought.strip(), answer.strip()


class ThesisAgent(BaseAgent):
    name = "thesis"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        system_prompt = (
            "あなたは修士論文執筆支援の専門アシスタントです。"
            "生命科学・抗体関連の背景・考察を、専門性を保ちつつ、"
            "日本語N1レベルで簡潔かつ論理的に書き直してください。"
            "出力は次のYAML形式に従ってください。\n"
            "thought: |-\n"
            "  （内部思考の要約：200字以内）\n"
            "answer: |-\n"
            "  （修論にそのまま貼れる形の本文）\n"
        )
        raw = llm.chat(
            [
                Message(role="system", content=system_prompt),
                Message(role="user", content=task),
            ]
        )

        thought, answer = self._parse_yaml_like(raw)
        return AgentResult(thought=thought, answer=answer, score=0.0)


class ESEditAgent(BaseAgent):
    name = "es_edit"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        system_prompt = (
            "あなたは製薬業界就活のエントリーシート添削アシスタントです。"
            "文系人事にも伝わるように専門用語を噛み砕き、"
            "独自性と論理性を両立した文章に整えてください。"
            "出力は次のYAML形式に従ってください。\n"
            "thought: |-\n"
            "  （文章構成・強みの整理：200字以内）\n"
            "answer: |-\n"
            "  （ESにそのまま貼れる文章）\n"
        )
        raw = llm.chat(
            [
                Message(role="system", content=system_prompt),
                Message(role="user", content=task),
            ]
        )

        thought, answer = self._parse_yaml_like(raw)
        return AgentResult(thought=thought, answer=answer, score=0.0)


class MiscAgent(BaseAgent):
    name = "misc"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:
        system_prompt = (
            "あなたは一般的な質問に答える汎用アシスタントです。"
            "日本語N1レベルで簡潔かつ正確に回答してください。\n"
            "出力形式:\n"
            "thought: |-\n"
            "answer: |-\n"
        )
        raw = llm.chat(
            [
                Message(role="system", content=system_prompt),
                Message(role="user", content=task),
            ]
        )
        thought, answer = self._parse_yaml_like(raw)
        return AgentResult(thought=thought, answer=answer, score=0.0)


class PaperFetcherAgent(BaseAgent):
    """Stub for paper-fetcher style agent."""

    name = "paper_fetcher"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:  # noqa: ARG002
        return AgentResult(
            thought="Gathering paper sources (stub)",
            answer=f"Stub: fetching papers for '{task}'",
            score=0.0,
            meta={"source": "paper_fetcher_stub"},
        )


class MyGPTPaperAnalyzerAgent(BaseAgent):
    """Stub for mygpt-paper-analyzer integration."""

    name = "mygpt_paper_analyzer"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:  # noqa: ARG002
        return AgentResult(
            thought="Analyzing papers via MyGPT (stub)",
            answer=f"Stub: analyzing papers for '{task}'",
            score=0.0,
            meta={"source": "mygpt_paper_analyzer_stub"},
        )


class JobAssistantAgent(BaseAgent):
    """Stub for job-hunting assistant (ES, interview prep)."""

    name = "job_assistant"

    def run_single(self, llm: LLMClient, task: str) -> AgentResult:  # noqa: ARG002
        return AgentResult(
            thought="Drafting job-hunting support output (stub)",
            answer=f"Stub: job assistance for '{task}'",
            score=0.0,
            meta={"source": "job_assistant_stub"},
        )
