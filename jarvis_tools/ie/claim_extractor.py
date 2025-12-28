"""Claim Extractor (P-04).

論文テキストから構造化された主張を抽出。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Claim:
    """単一の主張."""
    claim_id: str
    paper_id: str
    claim_text: str
    claim_type: str = "fact"  # fact, hypothesis, result, conclusion, methodology
    confidence: float = 0.0
    evidence_required: bool = True
    source_section: str = ""
    
    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "paper_id": self.paper_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "confidence": self.confidence,
            "evidence_required": self.evidence_required,
            "source_section": self.source_section,
        }


@dataclass
class ExtractionResult:
    """抽出結果."""
    claims: List[Claim] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class ClaimExtractor:
    """主張抽出器.
    
    論文テキストから以下の種類の主張を抽出:
    - fact: 実証された事実
    - hypothesis: 仮説・推測
    - result: 実験結果
    - conclusion: 結論
    - methodology: 方法論的主張
    """
    
    # 主張タイプの検出パターン
    CLAIM_PATTERNS = {
        "result": [
            r"we found that",
            r"our results show",
            r"we observed",
            r"we demonstrated",
            r"the data indicate",
            r"analysis revealed",
        ],
        "conclusion": [
            r"we conclude",
            r"in conclusion",
            r"these findings suggest",
            r"taken together",
            r"our study demonstrates",
        ],
        "hypothesis": [
            r"we hypothesize",
            r"it is possible that",
            r"may be",
            r"might be",
            r"could be",
            r"it is likely",
            r"we speculate",
        ],
        "methodology": [
            r"we used",
            r"we performed",
            r"we analyzed",
            r"was measured",
            r"were treated with",
        ],
    }
    
    def __init__(
        self,
        min_confidence: float = 0.5,
        max_claims_per_paper: int = 20,
    ):
        self.min_confidence = min_confidence
        self.max_claims = max_claims_per_paper
    
    def extract(
        self,
        text: str,
        paper_id: str,
        paper_title: str = "",
        sections: Optional[Dict[str, str]] = None,
    ) -> ExtractionResult:
        """テキストから主張を抽出.
        
        Args:
            text: 論文テキスト（または抽象）
            paper_id: 論文ID
            paper_title: 論文タイトル
            sections: セクション別テキスト（オプション）
            
        Returns:
            ExtractionResult
        """
        result = ExtractionResult()
        result.stats = {
            "paper_id": paper_id,
            "total_claims": 0,
            "by_type": {},
        }
        
        if not text:
            return result
        
        # 文に分割
        sentences = self._split_sentences(text)
        
        claim_count = 0
        for i, sentence in enumerate(sentences):
            if claim_count >= self.max_claims:
                break
            
            # 主張タイプを検出
            claim_type = self._detect_claim_type(sentence)
            
            # 主張らしい文のみ抽出
            if self._is_claim_sentence(sentence, claim_type):
                confidence = self._compute_confidence(sentence, claim_type)
                
                if confidence >= self.min_confidence:
                    claim = Claim(
                        claim_id=f"{paper_id}_claim_{claim_count}",
                        paper_id=paper_id,
                        claim_text=sentence.strip(),
                        claim_type=claim_type,
                        confidence=confidence,
                        evidence_required=(claim_type in ["fact", "result", "conclusion"]),
                    )
                    result.claims.append(claim)
                    claim_count += 1
                    
                    # 統計更新
                    result.stats["by_type"][claim_type] = result.stats["by_type"].get(claim_type, 0) + 1
        
        result.stats["total_claims"] = len(result.claims)
        
        return result
    
    def _split_sentences(self, text: str) -> List[str]:
        """テキストを文に分割."""
        # 簡易的な文分割
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _detect_claim_type(self, sentence: str) -> str:
        """文の主張タイプを検出."""
        sentence_lower = sentence.lower()
        
        for claim_type, patterns in self.CLAIM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    return claim_type
        
        return "fact"  # デフォルト
    
    def _is_claim_sentence(self, sentence: str, claim_type: str) -> bool:
        """主張として抽出すべき文か判定."""
        # 短すぎる文は除外
        if len(sentence) < 30:
            return False
        
        # 参照のみの文は除外
        if re.match(r'^[\[\d\],\s]+$', sentence):
            return False
        
        # 主張パターンにマッチするか
        sentence_lower = sentence.lower()
        
        # 何らかの主張指標があるか
        claim_indicators = [
            "show", "indicate", "suggest", "demonstrate", "reveal",
            "found", "observed", "concluded", "determined", "established",
            "significant", "important", "novel", "first",
        ]
        
        return any(ind in sentence_lower for ind in claim_indicators) or claim_type != "fact"
    
    def _compute_confidence(self, sentence: str, claim_type: str) -> float:
        """主張の信頼度を計算."""
        confidence = 0.5
        sentence_lower = sentence.lower()
        
        # 強い主張指標
        strong_indicators = ["significantly", "statistically", "demonstrated", "established"]
        if any(ind in sentence_lower for ind in strong_indicators):
            confidence += 0.2
        
        # 弱い表現（不確実性）
        weak_indicators = ["may", "might", "could", "possibly", "potentially"]
        if any(ind in sentence_lower for ind in weak_indicators):
            confidence -= 0.1
        
        # 数値データがあれば信頼度UP
        if re.search(r'\d+\.\d+|p\s*[<>=]\s*\d', sentence_lower):
            confidence += 0.15
        
        # タイプ別調整
        if claim_type == "result":
            confidence += 0.1
        elif claim_type == "hypothesis":
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def to_jsonl(self, result: ExtractionResult) -> str:
        """結果をJSONL形式に変換."""
        import json
        lines = []
        for claim in result.claims:
            lines.append(json.dumps(claim.to_dict(), ensure_ascii=False))
        return "\n".join(lines)


def extract_claims(
    text: str,
    paper_id: str,
    min_confidence: float = 0.5,
) -> ExtractionResult:
    """便利関数: 主張を抽出."""
    extractor = ClaimExtractor(min_confidence=min_confidence)
    return extractor.extract(text, paper_id)
