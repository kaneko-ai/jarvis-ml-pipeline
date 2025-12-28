"""Evidence Extractor (P-05).

根拠抽出モジュール。主張に対する根拠を抽出し、
locator（位置情報）を正規形で付与する。

Per BUNDLE_CONTRACT.md:
- evidence.jsonl必須キー: claim_id, paper_id, evidence_text, locator
- locator形式: {section, paragraph, chunk_id}
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis_core.prompts import PromptRegistry


@dataclass
class Locator:
    """根拠の位置情報（正規形）."""
    section: str = ""
    paragraph: int = 0
    chunk_id: str = ""
    page: Optional[int] = None
    sentence_id: Optional[int] = None  # 反復1で必須化
    char_start: Optional[int] = None  # 反復1で必須化
    char_end: Optional[int] = None    # 反復1で必須化
    
    def to_dict(self) -> dict:
        result = {
            "section": self.section,
            "paragraph": self.paragraph,
        }
        if self.chunk_id:
            result["chunk_id"] = self.chunk_id
        if self.page is not None:
            result["page"] = self.page
        if self.sentence_id is not None:
            result["sentence_id"] = self.sentence_id
        if self.char_start is not None and self.char_end is not None:
            result["char_start"] = self.char_start
            result["char_end"] = self.char_end
        return result
    
    @classmethod
    def from_dict(cls, d: dict) -> "Locator":
        return cls(
            section=d.get("section", ""),
            paragraph=d.get("paragraph", 0),
            chunk_id=d.get("chunk_id", ""),
            page=d.get("page"),
            sentence_id=d.get("sentence_id"),
            char_start=d.get("char_start"),
            char_end=d.get("char_end"),
        )


@dataclass
class Evidence:
    """単一の根拠."""
    claim_id: str
    paper_id: str
    evidence_text: str
    locator: Locator
    confidence: float = 0.0
    evidence_type: str = "direct"  # direct, indirect, inferred
    
    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "paper_id": self.paper_id,
            "evidence_text": self.evidence_text,
            "locator": self.locator.to_dict(),
            "confidence": self.confidence,
            "evidence_type": self.evidence_type,
        }


@dataclass
class ExtractionResult:
    """抽出結果."""
    evidence: List[Evidence] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class EvidenceExtractor:
    """根拠抽出器.
    
    主張テキストとチャンクを受け取り、
    関連する根拠を抽出・locator付与して返す。
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        prompt_registry: Optional[PromptRegistry] = None,
        min_confidence: float = 0.5,
        require_locator: bool = True,
    ):
        self.llm = llm_client
        self.prompts = prompt_registry or PromptRegistry()
        self.min_confidence = min_confidence
        self.require_locator = require_locator
    
    def extract(
        self,
        claims: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
        paper_id: str,
    ) -> ExtractionResult:
        """主張に対する根拠を抽出.
        
        Args:
            claims: 主張のリスト [{claim_id, claim_text, ...}]
            chunks: テキストチャンク [{chunk_id, text, section, ...}]
            paper_id: 論文ID
            
        Returns:
            ExtractionResult: 抽出された根拠と統計
        """
        result = ExtractionResult()
        result.stats = {
            "total_claims": len(claims),
            "total_chunks": len(chunks),
            "extracted_evidence": 0,
            "claims_without_evidence": 0,
            "locator_missing": 0,
        }
        
        if not claims or not chunks:
            return result
        
        for claim in claims:
            claim_id = claim.get("claim_id", "")
            claim_text = claim.get("claim_text", claim.get("text", ""))
            
            if not claim_text:
                continue
            
            # 各チャンクから関連根拠を探す
            claim_evidence = self._find_evidence_for_claim(
                claim_id=claim_id,
                claim_text=claim_text,
                chunks=chunks,
                paper_id=paper_id,
            )
            
            if claim_evidence:
                result.evidence.extend(claim_evidence)
                result.stats["extracted_evidence"] += len(claim_evidence)
            else:
                result.stats["claims_without_evidence"] += 1
                result.warnings.append({
                    "code": "NO_EVIDENCE",
                    "message": f"No evidence found for claim: {claim_id}",
                    "severity": "warning",
                })
        
        # Locator欠落チェック
        for ev in result.evidence:
            if not ev.locator.section:
                result.stats["locator_missing"] += 1
                if self.require_locator:
                    result.warnings.append({
                        "code": "LOCATOR_MISSING",
                        "message": f"Missing locator for evidence: {ev.claim_id}",
                        "severity": "warning",
                    })
        
        return result
    
    def _find_evidence_for_claim(
        self,
        claim_id: str,
        claim_text: str,
        chunks: List[Dict[str, Any]],
        paper_id: str,
    ) -> List[Evidence]:
        """単一の主張に対する根拠を検索.
        
        Hybrid approach:
        1. キーワードベースの初期フィルタ
        2. セマンティック類似度（利用可能な場合）
        3. LLM検証（利用可能な場合）
        """
        evidence_list = []
        
        # キーワード抽出（シンプルなアプローチ）
        keywords = self._extract_keywords(claim_text)
        
        for chunk in chunks:
            chunk_text = chunk.get("text", "")
            chunk_id = chunk.get("chunk_id", "")
            section = chunk.get("section", "Unknown")
            paragraph = chunk.get("paragraph_index", 0)
            
            # キーワードマッチング
            score = self._compute_relevance(claim_text, chunk_text, keywords)
            
            if score >= self.min_confidence:
                # 根拠テキストをクリーンアップ
                evidence_text = self._extract_relevant_passage(claim_text, chunk_text)
                
                locator = Locator(
                    section=section,
                    paragraph=paragraph,
                    chunk_id=chunk_id,
                    page=chunk.get("page"),
                )
                
                evidence = Evidence(
                    claim_id=claim_id,
                    paper_id=paper_id,
                    evidence_text=evidence_text,
                    locator=locator,
                    confidence=score,
                    evidence_type="direct" if score > 0.8 else "indirect",
                )
                evidence_list.append(evidence)
        
        # 信頼度でソートし、上位を返す
        evidence_list.sort(key=lambda e: e.confidence, reverse=True)
        return evidence_list[:3]  # 最大3件
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出."""
        # 簡易的なキーワード抽出
        words = re.findall(r'\b[A-Za-z][A-Za-z0-9-]+\b', text.lower())
        
        # ストップワード除去
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'this', 'that', 'these', 'those', 'which', 'who', 'what',
            'when', 'where', 'why', 'how', 'and', 'or', 'but', 'if',
            'then', 'else', 'for', 'with', 'by', 'from', 'to', 'of',
            'in', 'on', 'at', 'as', 'not', 'no', 'yes',
        }
        
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return list(set(keywords))
    
    def _compute_relevance(
        self,
        claim_text: str,
        chunk_text: str,
        keywords: List[str],
    ) -> float:
        """関連度スコアを計算."""
        if not chunk_text:
            return 0.0
        
        chunk_lower = chunk_text.lower()
        
        # キーワードマッチ率
        if not keywords:
            return 0.0
        
        matches = sum(1 for kw in keywords if kw in chunk_lower)
        keyword_score = matches / len(keywords)
        
        # 長さペナルティ（極端に短いチャンクは避ける）
        length_factor = min(1.0, len(chunk_text) / 100)
        
        # 最終スコア
        return keyword_score * 0.8 + length_factor * 0.2
    
    def _extract_relevant_passage(self, claim_text: str, chunk_text: str) -> str:
        """チャンクから関連する文を抽出."""
        # 文に分割
        sentences = re.split(r'(?<=[.!?])\s+', chunk_text)
        
        if len(sentences) <= 2:
            return chunk_text.strip()
        
        # 主張のキーワードを含む文を優先
        keywords = self._extract_keywords(claim_text)
        
        scored_sentences = []
        for sent in sentences:
            sent_lower = sent.lower()
            score = sum(1 for kw in keywords if kw in sent_lower)
            scored_sentences.append((score, sent))
        
        # スコア上位2-3文を結合
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s[1] for s in scored_sentences[:3] if s[0] > 0]
        
        if top_sentences:
            return " ".join(top_sentences).strip()
        
        # フォールバック：最初の2文
        return " ".join(sentences[:2]).strip()
    
    def to_jsonl(self, result: ExtractionResult) -> str:
        """結果をJSONL形式に変換."""
        lines = []
        for ev in result.evidence:
            lines.append(json.dumps(ev.to_dict(), ensure_ascii=False))
        return "\n".join(lines)


def extract_evidence(
    claims: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    paper_id: str,
    min_confidence: float = 0.5,
) -> ExtractionResult:
    """便利関数: 根拠抽出を実行."""
    extractor = EvidenceExtractor(min_confidence=min_confidence)
    return extractor.extract(claims, chunks, paper_id)
