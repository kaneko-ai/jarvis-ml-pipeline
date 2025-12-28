"""Summarizers (P-07).

3種の要約生成:
- 300字要約
- 詳細解説
- NotebookLM台本
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis_core.prompts import get_registry


@dataclass
class SummaryOutput:
    """要約出力."""
    summary_300: str = ""
    summary_detailed: str = ""
    notebooklm_script: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "summary_300": self.summary_300,
            "summary_detailed": self.summary_detailed,
            "notebooklm_script": self.notebooklm_script,
            "metadata": self.metadata,
        }


class Summarizer:
    """要約生成器.
    
    Prompt Registry経由でテンプレートを使用。
    LLMがない場合はテンプレートのみ返却。
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
    ):
        self.llm = llm_client
        self.prompts = get_registry()
    
    def generate_all(
        self,
        topic: str,
        claims: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> SummaryOutput:
        """3種の要約を全て生成.
        
        Args:
            topic: トピック/クエリ
            claims: 主張リスト
            evidence: 根拠リスト
            
        Returns:
            SummaryOutput
        """
        # 主張と根拠をフォーマット
        claims_text = self._format_claims_with_evidence(claims, evidence)
        
        output = SummaryOutput(
            metadata={
                "topic": topic,
                "claims_count": len(claims),
                "evidence_count": len(evidence),
            }
        )
        
        # 300字要約
        output.summary_300 = self.generate_300(topic, claims_text)
        
        # 詳細解説
        output.summary_detailed = self.generate_detailed(topic, claims_text)
        
        # NotebookLM台本
        output.notebooklm_script = self.generate_notebooklm(topic, claims_text)
        
        return output
    
    def generate_300(self, topic: str, claims_text: str) -> str:
        """300字要約を生成."""
        if self.llm:
            prompt = self.prompts.render(
                "summarizer_300",
                topic=topic,
                claims=claims_text,
            )
            # TODO: LLM呼び出し
            # return self.llm.generate(prompt)
        
        # フォールバック：テンプレートベース生成
        return self._template_300(topic, claims_text)
    
    def generate_detailed(self, topic: str, claims_text: str) -> str:
        """詳細解説を生成."""
        if self.llm:
            prompt = self.prompts.render(
                "summarizer_detailed",
                topic=topic,
                claims=claims_text,
            )
            # TODO: LLM呼び出し
        
        return self._template_detailed(topic, claims_text)
    
    def generate_notebooklm(self, topic: str, claims_text: str) -> str:
        """NotebookLM台本を生成."""
        if self.llm:
            prompt = self.prompts.render(
                "summarizer_notebooklm",
                topic=topic,
                claims=claims_text,
            )
            # TODO: LLM呼び出し
        
        return self._template_notebooklm(topic, claims_text)
    
    def _format_claims_with_evidence(
        self,
        claims: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> str:
        """主張と根拠をフォーマット."""
        evidence_by_claim = {}
        for ev in evidence:
            claim_id = ev.get("claim_id", "")
            if claim_id not in evidence_by_claim:
                evidence_by_claim[claim_id] = []
            evidence_by_claim[claim_id].append(ev.get("evidence_text", ""))
        
        lines = []
        for claim in claims:
            claim_id = claim.get("claim_id", "")
            claim_text = claim.get("claim_text", "")
            paper_id = claim.get("paper_id", "")
            
            lines.append(f"- {claim_text} [{paper_id}]")
            
            if claim_id in evidence_by_claim:
                for ev_text in evidence_by_claim[claim_id][:2]:
                    lines.append(f"  根拠: {ev_text[:100]}...")
        
        return "\n".join(lines)
    
    def _template_300(self, topic: str, claims_text: str) -> str:
        """300字テンプレート生成."""
        # 主張から最初の3件を抽出
        lines = claims_text.split("\n")
        claim_lines = [l for l in lines if l.startswith("- ")][:3]
        
        summary_parts = []
        for cl in claim_lines:
            # [paper_id]を除去して50字に切り詰め
            clean = cl.replace("- ", "").split("[")[0].strip()
            if len(clean) > 50:
                clean = clean[:47] + "..."
            summary_parts.append(clean)
        
        if not summary_parts:
            return f"「{topic}」について、現時点で十分な根拠のある情報が見つかりませんでした。"
        
        n_claims = len(claim_lines)
        summary = f"「{topic}」について{n_claims}件の知見が得られた。"
        summary += "".join(summary_parts[:2])
        
        # 300字以内に調整
        if len(summary) > 300:
            summary = summary[:297] + "..."
        
        return summary
    
    def _template_detailed(self, topic: str, claims_text: str) -> str:
        """詳細テンプレート生成."""
        lines = [
            f"# {topic}",
            "",
            "## 背景",
            f"本レポートは「{topic}」に関する文献調査の結果である。",
            "",
            "## 主要な発見",
            "",
        ]
        
        claim_lines = claims_text.split("\n")
        for cl in claim_lines:
            if cl.startswith("- "):
                lines.append(cl)
            elif cl.strip().startswith("根拠:"):
                lines.append(f"  {cl.strip()}")
        
        lines.extend([
            "",
            "## 限界と未解決点",
            "- 調査した論文数が限られている可能性があります",
            "- 追加の検証が必要な主張があります",
            "",
            "## 次の問い",
            f"- 「{topic}」のさらなる機序解明",
            "- 臨床応用に向けた課題の特定",
        ])
        
        return "\n".join(lines)
    
    def _template_notebooklm(self, topic: str, claims_text: str) -> str:
        """NotebookLM台本テンプレート生成."""
        claim_lines = [l for l in claims_text.split("\n") if l.startswith("- ")][:5]
        
        lines = [
            f"# NotebookLM風対話: {topic}",
            "",
            "---",
            "",
            f"**A:** 今日は「{topic}」について調べてきたんですよね？",
            "",
            f"**B:** はい、いくつか興味深い知見が見つかりました。",
            "",
        ]
        
        for i, cl in enumerate(claim_lines):
            clean = cl.replace("- ", "").split("[")[0].strip()
            if i == 0:
                lines.append(f"**B:** まず重要なのは、{clean}")
                lines.append("")
                lines.append("**A:** なるほど、それは興味深いですね。他には？")
                lines.append("")
            else:
                lines.append(f"**B:** また、{clean}")
                lines.append("")
        
        lines.extend([
            "**A:** 今後の研究ではどこに注目すべきでしょうか？",
            "",
            f"**B:** {topic}の臨床応用に向けた課題の解明が重要だと思います。",
            "",
            "---",
            "*このスクリプトはテンプレートから自動生成されました*",
        ])
        
        return "\n".join(lines)


def generate_summaries(
    topic: str,
    claims: List[Dict[str, Any]],
    evidence: List[Dict[str, Any]],
) -> SummaryOutput:
    """便利関数: 3種の要約を生成."""
    summarizer = Summarizer()
    return summarizer.generate_all(topic, claims, evidence)
