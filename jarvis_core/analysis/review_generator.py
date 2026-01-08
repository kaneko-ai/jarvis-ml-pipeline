"""
JARVIS Review Generator

7. レビュー自動生成: 多粒度要約（300字/1000字/初心者向け）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ReviewOutput:
    """レビュー出力."""
    summary_short: str  # 300字
    summary_long: str  # 1000字
    summary_beginner: str  # 初心者向け
    key_findings: list[str]
    methodology_summary: str
    limitations: list[str]
    future_directions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_short": self.summary_short,
            "summary_long": self.summary_long,
            "summary_beginner": self.summary_beginner,
            "key_findings": self.key_findings,
            "methodology_summary": self.methodology_summary,
            "limitations": self.limitations,
            "future_directions": self.future_directions,
        }

    def to_markdown(self) -> str:
        """Markdown形式で出力."""
        lines = [
            "# Literature Review",
            "",
            "## Summary (Short)",
            self.summary_short,
            "",
            "## Summary (Long)",
            self.summary_long,
            "",
            "## Summary (For Beginners)",
            self.summary_beginner,
            "",
            "## Key Findings",
        ]
        for finding in self.key_findings:
            lines.append(f"- {finding}")

        lines.extend([
            "",
            "## Methodology",
            self.methodology_summary,
            "",
            "## Limitations",
        ])
        for limitation in self.limitations:
            lines.append(f"- {limitation}")

        lines.extend([
            "",
            "## Future Directions",
        ])
        for direction in self.future_directions:
            lines.append(f"- {direction}")

        return "\n".join(lines)


class ReviewGenerator:
    """レビュー生成器.
    
    論文群から多粒度レビューを生成
    """

    SUMMARY_PROMPT_SHORT = """
以下の論文情報から、300字以内の要約を作成してください。
重要なポイントのみを簡潔にまとめてください。

{content}
"""

    SUMMARY_PROMPT_LONG = """
以下の論文情報から、1000字程度の詳細な要約を作成してください。
背景、方法、結果、考察を含めてください。

{content}
"""

    SUMMARY_PROMPT_BEGINNER = """
以下の論文情報を、専門知識のない一般の方にもわかるように
平易な言葉で説明してください（300字程度）。
専門用語は避け、例えを使って説明してください。

{content}
"""

    def __init__(self, llm_client=None):
        """初期化."""
        self.llm_client = llm_client

    def generate_review(
        self,
        papers: list[dict[str, Any]],
        claims: list[dict[str, Any]],
    ) -> ReviewOutput:
        """レビューを生成.
        
        Args:
            papers: 論文リスト
            claims: 主張リスト
        
        Returns:
            レビュー出力
        """
        # コンテンツを構築
        content = self._build_content(papers, claims)

        if self.llm_client:
            return self._generate_with_llm(content, papers, claims)
        else:
            return self._generate_rule_based(content, papers, claims)

    def _build_content(
        self,
        papers: list[dict[str, Any]],
        claims: list[dict[str, Any]],
    ) -> str:
        """レビュー用コンテンツを構築."""
        lines = []

        for paper in papers[:5]:
            lines.append(f"Title: {paper.get('title', 'Unknown')}")
            lines.append(f"Year: {paper.get('year', 'Unknown')}")
            lines.append(f"Abstract: {paper.get('abstract', '')[:500]}")
            lines.append("")

        if claims:
            lines.append("Key Claims:")
            for claim in claims[:10]:
                lines.append(f"- {claim.get('claim_text', '')}")

        return "\n".join(lines)

    def _generate_with_llm(
        self,
        content: str,
        papers: list[dict[str, Any]],
        claims: list[dict[str, Any]],
    ) -> ReviewOutput:
        """LLMで生成."""
        try:
            summary_short = self.llm_client.generate(
                self.SUMMARY_PROMPT_SHORT.format(content=content)
            )
            summary_long = self.llm_client.generate(
                self.SUMMARY_PROMPT_LONG.format(content=content)
            )
            summary_beginner = self.llm_client.generate(
                self.SUMMARY_PROMPT_BEGINNER.format(content=content)
            )

            return ReviewOutput(
                summary_short=summary_short,
                summary_long=summary_long,
                summary_beginner=summary_beginner,
                key_findings=[c.get("claim_text", "")[:100] for c in claims[:5]],
                methodology_summary="Methods described in the papers.",
                limitations=["Sample size", "Study design"],
                future_directions=["Further research needed"],
            )

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_rule_based(content, papers, claims)

    def _generate_rule_based(
        self,
        content: str,
        papers: list[dict[str, Any]],
        claims: list[dict[str, Any]],
    ) -> ReviewOutput:
        """ルールベースで生成."""
        # 論文タイトルから要約を生成
        titles = [p.get("title", "") for p in papers[:3]]

        summary_short = f"This review covers {len(papers)} papers. " + \
                        f"Key topics include: {', '.join(titles[:2])}."

        summary_long = f"This comprehensive review analyzes {len(papers)} papers " + \
                       "related to the research topic. " + \
                       f"The studies include: {'; '.join(titles)}. " + \
                       f"A total of {len(claims)} key claims were identified."

        summary_beginner = "This research looks at important scientific questions. " + \
                          "Scientists studied these topics to help us understand better."

        key_findings = [c.get("claim_text", "")[:100] for c in claims[:5]]

        return ReviewOutput(
            summary_short=summary_short[:300],
            summary_long=summary_long[:1000],
            summary_beginner=summary_beginner[:300],
            key_findings=key_findings,
            methodology_summary="Various research methods were employed.",
            limitations=["Limited scope", "Need for replication"],
            future_directions=["Expand sample size", "Long-term studies"],
        )
