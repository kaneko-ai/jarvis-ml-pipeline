"""
JARVIS Summarizer Plugin - Multi-grain Summarization

多粒度要約（300字/1000字/章別）、比較要約、初学者向け言い換え。
全出力にevidence_links必須。
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, Claim, EvidenceLink, RuntimeConfig, TaskContext
)


@dataclass
class Summary:
    """要約結果."""
    summary_id: str
    text: str
    length: int  # 文字数
    grain: str  # short, medium, long, section
    source_doc_ids: List[str]
    evidence: List[EvidenceLink] = field(default_factory=list)


class MultiGrainSummarizer:
    """
    多粒度要約器.
    
    - 短文 (~300字): キーポイントのみ
    - 中文 (~1000字): 主要な結果と方法
    - 長文 (~2000字): 詳細な解説
    - 章別: 各セクションの要約
    """
    
    def __init__(self):
        self.llm = None
        
        # Try to load LLM
        try:
            import google.generativeai as genai
            import os
            if os.environ.get("GEMINI_API_KEY"):
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
                self.llm = genai.GenerativeModel("gemini-1.5-flash")
        except (ImportError, Exception):
            pass
    
    def summarize(self, text: str, doc_id: str, 
                  target_length: int = 300,
                  grain: str = "short") -> Summary:
        """
        テキストを要約.
        
        Args:
            text: 入力テキスト
            doc_id: ドキュメントID
            target_length: 目標文字数
            grain: 粒度 (short/medium/long)
        
        Returns:
            Summary with evidence_links
        """
        if self.llm:
            return self._summarize_with_llm(text, doc_id, target_length, grain)
        else:
            return self._summarize_extractive(text, doc_id, target_length, grain)
    
    def _summarize_with_llm(self, text: str, doc_id: str,
                            target_length: int, grain: str) -> Summary:
        """LLMで要約."""
        prompt = f"""以下のテキストを{target_length}字程度で要約してください。
重要なポイントを漏らさず、根拠を明示してください。

テキスト:
{text[:5000]}

要約:"""
        
        try:
            response = self.llm.generate_content(prompt)
            summary_text = response.text
        except Exception:
            return self._summarize_extractive(text, doc_id, target_length, grain)
        
        # Create evidence links
        evidence = self._create_evidence_links(text, summary_text, doc_id)
        
        return Summary(
            summary_id=f"sum-{uuid.uuid4().hex[:8]}",
            text=summary_text,
            length=len(summary_text),
            grain=grain,
            source_doc_ids=[doc_id],
            evidence=evidence
        )
    
    def _summarize_extractive(self, text: str, doc_id: str,
                              target_length: int, grain: str) -> Summary:
        """抽出型要約（LLMなし）."""
        sentences = re.split(r'[.!?。！？]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Score sentences by position and keyword importance
        scored = []
        keywords = ["result", "show", "demonstrate", "conclude", "significant", 
                   "important", "novel", "first", "major", "clinical"]
        
        for i, sent in enumerate(sentences):
            score = 0.0
            # Position score (first and last sentences important)
            if i < 3:
                score += 2.0
            if i >= len(sentences) - 3:
                score += 1.5
            
            # Keyword score
            sent_lower = sent.lower()
            for kw in keywords:
                if kw in sent_lower:
                    score += 1.0
            
            scored.append((sent, score))
        
        # Sort by score and select top sentences
        scored.sort(key=lambda x: x[1], reverse=True)
        
        selected = []
        total_len = 0
        for sent, score in scored:
            if total_len + len(sent) > target_length:
                break
            selected.append(sent)
            total_len += len(sent)
        
        summary_text = ". ".join(selected) + "."
        
        # Create evidence
        evidence = []
        for sent in selected[:3]:
            idx = text.find(sent)
            if idx >= 0:
                evidence.append(EvidenceLink(
                    doc_id=doc_id,
                    section="extracted",
                    chunk_id=f"{doc_id}_sum",
                    start=idx,
                    end=idx + len(sent),
                    confidence=0.8,
                    text=sent[:100]
                ))
        
        return Summary(
            summary_id=f"sum-{uuid.uuid4().hex[:8]}",
            text=summary_text,
            length=len(summary_text),
            grain=grain,
            source_doc_ids=[doc_id],
            evidence=evidence
        )
    
    def _create_evidence_links(self, source: str, summary: str, 
                               doc_id: str) -> List[EvidenceLink]:
        """要約から根拠リンクを作成."""
        evidence = []
        
        # Find matching phrases
        summary_words = set(summary.lower().split())
        sentences = re.split(r'[.!?]', source)
        
        for sent in sentences:
            sent_words = set(sent.lower().split())
            overlap = len(summary_words & sent_words) / len(summary_words) if summary_words else 0
            
            if overlap > 0.3:
                idx = source.find(sent)
                if idx >= 0:
                    evidence.append(EvidenceLink(
                        doc_id=doc_id,
                        section="source",
                        chunk_id=f"{doc_id}_src",
                        start=idx,
                        end=idx + len(sent),
                        confidence=overlap,
                        text=sent[:100]
                    ))
        
        return evidence[:5]
    
    def summarize_sections(self, sections: Dict[str, str], 
                           doc_id: str) -> Dict[str, Summary]:
        """セクション別に要約."""
        summaries = {}
        
        section_targets = {
            "Abstract": 150,
            "Introduction": 200,
            "Methods": 300,
            "Results": 400,
            "Discussion": 300,
            "Conclusion": 150
        }
        
        for section_name, section_text in sections.items():
            target = section_targets.get(section_name, 200)
            summaries[section_name] = self.summarize(
                section_text, doc_id, target, grain="section"
            )
        
        return summaries


class ComparativeSummarizer:
    """比較要約器."""
    
    def compare(self, papers: List[Dict[str, str]]) -> Dict[str, Any]:
        """複数論文を比較要約."""
        agreements = []
        disagreements = []
        
        # Simple keyword-based comparison
        all_claims = []
        for paper in papers:
            doc_id = paper.get("doc_id", "")
            text = paper.get("abstract", "")
            
            # Extract key findings
            patterns = [
                r"(?:we|results?)\s+(?:show|demonstrate|found)\s+that\s+([^.]+\.)",
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    all_claims.append((doc_id, match))
        
        # Group similar claims
        for i, (doc1, claim1) in enumerate(all_claims):
            for doc2, claim2 in all_claims[i+1:]:
                similarity = self._text_similarity(claim1, claim2)
                if similarity > 0.5:
                    agreements.append({
                        "docs": [doc1, doc2],
                        "claims": [claim1, claim2],
                        "similarity": similarity
                    })
                elif similarity > 0.2:
                    disagreements.append({
                        "docs": [doc1, doc2],
                        "claims": [claim1, claim2],
                        "type": "potential_disagreement"
                    })
        
        return {
            "agreements": agreements,
            "disagreements": disagreements,
            "total_papers": len(papers),
            "total_claims": len(all_claims)
        }
    
    def _text_similarity(self, t1: str, t2: str) -> float:
        """テキスト類似度."""
        words1 = set(t1.lower().split())
        words2 = set(t2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)


class BeginnerSimplifier:
    """初学者向け言い換え."""
    
    # 専門用語 → 平易な表現
    SIMPLIFICATIONS = {
        "oncogene": "がんを引き起こす遺伝子",
        "metastasis": "がんの転移",
        "apoptosis": "細胞の自然死（プログラムされた死）",
        "biomarker": "病気の指標となる物質",
        "in vitro": "試験管内の実験",
        "in vivo": "生体内の実験",
        "cohort": "研究対象グループ",
        "randomized": "ランダムに割り当てた",
        "placebo": "偽薬（効果のない比較用の薬）",
        "efficacy": "有効性",
        "adverse event": "副作用",
        "pharmacokinetics": "薬の体内動態",
    }
    
    def simplify(self, text: str) -> str:
        """テキストを簡略化."""
        result = text
        
        for term, simple in self.SIMPLIFICATIONS.items():
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            result = pattern.sub(f"{term}（{simple}）", result)
        
        return result


class SummarizerPlugin:
    """Summarizer統合プラグイン."""
    
    def __init__(self):
        self.multi_grain = MultiGrainSummarizer()
        self.comparative = ComparativeSummarizer()
        self.simplifier = BeginnerSimplifier()
        self.is_active = False
    
    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        self.is_active = True
    
    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """要約を実行."""
        delta: ArtifactsDelta = {
            "summaries": {},
            "comparison": None,
            "simplified": {}
        }
        
        # Multi-grain summaries for each paper
        for paper in artifacts.papers:
            paper_text = paper.abstract or ""
            for section_text in paper.sections.values():
                paper_text += " " + section_text
            
            # Short summary (300 chars)
            short = self.multi_grain.summarize(paper_text, paper.doc_id, 300, "short")
            
            # Medium summary (1000 chars)
            medium = self.multi_grain.summarize(paper_text, paper.doc_id, 1000, "medium")
            
            # Section summaries
            section_sums = self.multi_grain.summarize_sections(paper.sections, paper.doc_id)
            
            delta["summaries"][paper.doc_id] = {
                "short": {
                    "text": short.text,
                    "evidence": [e.to_dict() for e in short.evidence]
                },
                "medium": {
                    "text": medium.text,
                    "evidence": [e.to_dict() for e in medium.evidence]
                },
                "sections": {
                    k: {"text": v.text, "evidence": [e.to_dict() for e in v.evidence]}
                    for k, v in section_sums.items()
                }
            }
            
            # Simplified version
            simplified = self.simplifier.simplify(short.text)
            delta["simplified"][paper.doc_id] = simplified
            
            # Store in artifacts
            artifacts.summaries[paper.doc_id] = short.text
        
        # Comparative summary
        if len(artifacts.papers) > 1:
            papers_data = [
                {"doc_id": p.doc_id, "abstract": p.abstract or ""}
                for p in artifacts.papers
            ]
            delta["comparison"] = self.comparative.compare(papers_data)
        
        return delta
    
    def deactivate(self) -> None:
        self.is_active = False


def get_summarizer_plugin() -> SummarizerPlugin:
    return SummarizerPlugin()
