"""
JARVIS Scientific Validity - Counterevidence Search

M5: 科学的妥当性のための反証探索
- 主張ごとに反対方向の研究を探索
- 論争マップの生成
- 両論併記の出力
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class EvidenceStance(Enum):
    """エビデンスの立場."""
    SUPPORTING = "supporting"
    OPPOSING = "opposing"
    NEUTRAL = "neutral"
    INCONCLUSIVE = "inconclusive"


class ControversyLevel(Enum):
    """論争レベル."""
    NONE = "none"              # 論争なし（コンセンサス）
    LOW = "low"                # 軽微な論争
    MODERATE = "moderate"      # 中程度の論争
    HIGH = "high"              # 高い論争
    UNRESOLVED = "unresolved"  # 未解決


@dataclass
class CounterevidenceResult:
    """反証探索結果."""
    claim_id: str
    claim_text: str
    supporting_count: int = 0
    opposing_count: int = 0
    neutral_count: int = 0
    supporting_refs: List[Dict[str, Any]] = field(default_factory=list)
    opposing_refs: List[Dict[str, Any]] = field(default_factory=list)
    controversy_level: ControversyLevel = ControversyLevel.NONE
    conclusion_status: str = "confirmed"  # confirmed, contested, inconclusive


@dataclass
class ControversyMapEntry:
    """論争マップエントリ."""
    topic: str
    claim_text: str
    supporting_arguments: List[Dict[str, Any]] = field(default_factory=list)
    opposing_arguments: List[Dict[str, Any]] = field(default_factory=list)
    undecided_points: List[str] = field(default_factory=list)
    current_consensus: Optional[str] = None
    controversy_level: ControversyLevel = ControversyLevel.NONE
    provenance: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ControversyMap:
    """論争マップ."""
    run_id: str
    entries: List[ControversyMapEntry] = field(default_factory=list)
    has_high_controversy: bool = False
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換."""
        return {
            "run_id": self.run_id,
            "entries": [
                {
                    "topic": e.topic,
                    "claim_text": e.claim_text,
                    "supporting_arguments": e.supporting_arguments,
                    "opposing_arguments": e.opposing_arguments,
                    "undecided_points": e.undecided_points,
                    "current_consensus": e.current_consensus,
                    "controversy_level": e.controversy_level.value,
                    "provenance": e.provenance
                }
                for e in self.entries
            ],
            "has_high_controversy": self.has_high_controversy,
            "summary": self.summary
        }


class CounterevidenceSearcher:
    """反証探索器."""
    
    # 反対方向を示すキーワード
    OPPOSITION_KEYWORDS = [
        "however", "but", "contrary", "contradict", "oppose",
        "fail", "failed", "not support", "no effect", "negative",
        "no significant", "no difference", "ineffective"
    ]
    
    # 支持方向を示すキーワード
    SUPPORT_KEYWORDS = [
        "support", "confirm", "consistent", "agree", "positive",
        "significant", "effective", "demonstrate", "show"
    ]
    
    def __init__(self):
        """初期化."""
        pass
    
    def generate_counter_query(self, claim_text: str) -> str:
        """
        反証用検索クエリを生成.
        
        Args:
            claim_text: 主張テキスト
        
        Returns:
            反証検索用クエリ
        """
        # 否定語を追加
        negation_terms = ["NOT", "fail", "negative", "no effect", "contradict"]
        
        # 主要キーワードを抽出
        words = re.findall(r'\b[a-zA-Z]{4,}\b', claim_text.lower())
        stopwords = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'have', 'been'}
        keywords = [w for w in words if w not in stopwords][:5]
        
        if keywords:
            base_query = " ".join(keywords)
            return f"({base_query}) AND ({' OR '.join(negation_terms[:3])})"
        
        return claim_text
    
    def classify_stance(
        self, 
        claim_text: str, 
        evidence_text: str
    ) -> Tuple[EvidenceStance, float]:
        """
        エビデンスの立場を分類.
        
        Args:
            claim_text: 主張テキスト
            evidence_text: エビデンステキスト
        
        Returns:
            (立場, 確信度)
        """
        evidence_lower = evidence_text.lower()
        
        # 反対キーワードのカウント
        opposition_count = sum(
            1 for kw in self.OPPOSITION_KEYWORDS 
            if kw in evidence_lower
        )
        
        # 支持キーワードのカウント
        support_count = sum(
            1 for kw in self.SUPPORT_KEYWORDS 
            if kw in evidence_lower
        )
        
        total = opposition_count + support_count
        if total == 0:
            return EvidenceStance.NEUTRAL, 0.5
        
        support_ratio = support_count / total
        
        if opposition_count > support_count * 1.5:
            return EvidenceStance.OPPOSING, min(0.9, 0.5 + opposition_count * 0.1)
        elif support_count > opposition_count * 1.5:
            return EvidenceStance.SUPPORTING, min(0.9, 0.5 + support_count * 0.1)
        else:
            return EvidenceStance.INCONCLUSIVE, 0.5
    
    def assess_controversy(
        self, 
        supporting_count: int, 
        opposing_count: int
    ) -> ControversyLevel:
        """
        論争レベルを評価.
        
        Args:
            supporting_count: 支持エビデンス数
            opposing_count: 反対エビデンス数
        
        Returns:
            論争レベル
        """
        total = supporting_count + opposing_count
        
        if total == 0:
            return ControversyLevel.NONE
        
        if opposing_count == 0:
            return ControversyLevel.NONE  # コンセンサス
        
        opposition_ratio = opposing_count / total
        
        if opposition_ratio < 0.1:
            return ControversyLevel.LOW
        elif opposition_ratio < 0.3:
            return ControversyLevel.MODERATE
        elif opposition_ratio < 0.5:
            return ControversyLevel.HIGH
        else:
            return ControversyLevel.UNRESOLVED
    
    def search_counterevidence(
        self,
        claim_id: str,
        claim_text: str,
        evidence_texts: List[str]
    ) -> CounterevidenceResult:
        """
        反証を探索.
        
        Args:
            claim_id: 主張ID
            claim_text: 主張テキスト
            evidence_texts: エビデンステキストリスト
        
        Returns:
            反証探索結果
        """
        result = CounterevidenceResult(
            claim_id=claim_id,
            claim_text=claim_text
        )
        
        for i, evidence in enumerate(evidence_texts):
            stance, confidence = self.classify_stance(claim_text, evidence)
            
            ref_info = {
                "index": i,
                "stance": stance.value,
                "confidence": confidence,
                "text_preview": evidence[:200]
            }
            
            if stance == EvidenceStance.SUPPORTING:
                result.supporting_count += 1
                result.supporting_refs.append(ref_info)
            elif stance == EvidenceStance.OPPOSING:
                result.opposing_count += 1
                result.opposing_refs.append(ref_info)
            else:
                result.neutral_count += 1
        
        # 論争レベルを評価
        result.controversy_level = self.assess_controversy(
            result.supporting_count,
            result.opposing_count
        )
        
        # 結論ステータスを決定
        if result.controversy_level == ControversyLevel.NONE:
            result.conclusion_status = "confirmed"
        elif result.controversy_level in [ControversyLevel.LOW, ControversyLevel.MODERATE]:
            result.conclusion_status = "contested"
        else:
            result.conclusion_status = "inconclusive"
        
        return result


class ControversyMapGenerator:
    """論争マップ生成器."""
    
    def __init__(self):
        """初期化."""
        self.searcher = CounterevidenceSearcher()
    
    def generate(
        self,
        run_id: str,
        claims: List[Dict[str, Any]],
        evidence_by_claim: Dict[str, List[str]]
    ) -> ControversyMap:
        """
        論争マップを生成.
        
        Args:
            run_id: 実行ID
            claims: 主張リスト
            evidence_by_claim: claim_id -> エビデンステキストリスト
        
        Returns:
            論争マップ
        """
        controversy_map = ControversyMap(run_id=run_id)
        high_controversy_count = 0
        
        for claim in claims:
            claim_id = claim.get("claim_id", "")
            claim_text = claim.get("claim_text", "")
            
            evidence_texts = evidence_by_claim.get(claim_id, [])
            
            # 反証探索
            counter_result = self.searcher.search_counterevidence(
                claim_id, claim_text, evidence_texts
            )
            
            # 論争がある場合のみエントリを追加
            if counter_result.controversy_level != ControversyLevel.NONE:
                entry = ControversyMapEntry(
                    topic=claim_text[:100],
                    claim_text=claim_text,
                    supporting_arguments=[
                        {"text": r["text_preview"], "confidence": r["confidence"]}
                        for r in counter_result.supporting_refs
                    ],
                    opposing_arguments=[
                        {"text": r["text_preview"], "confidence": r["confidence"]}
                        for r in counter_result.opposing_refs
                    ],
                    controversy_level=counter_result.controversy_level,
                    current_consensus=(
                        "Majority supporting" 
                        if counter_result.supporting_count > counter_result.opposing_count 
                        else "Contested"
                    )
                )
                
                controversy_map.entries.append(entry)
                
                if counter_result.controversy_level in [ControversyLevel.HIGH, ControversyLevel.UNRESOLVED]:
                    high_controversy_count += 1
        
        controversy_map.has_high_controversy = high_controversy_count > 0
        controversy_map.summary = (
            f"{len(controversy_map.entries)} controversial topics found, "
            f"{high_controversy_count} high controversy"
        )
        
        return controversy_map


def check_one_sided_conclusion(
    claims: List[Dict[str, Any]],
    controversy_map: ControversyMap
) -> Tuple[bool, List[str]]:
    """
    一方的結論チェック.
    
    Args:
        claims: 主張リスト
        controversy_map: 論争マップ
    
    Returns:
        (違反あり, 違反主張IDリスト)
    """
    violations = []
    
    # 高い論争がある主張がmain_conclusionにあるかチェック
    high_controversy_topics = {
        e.claim_text[:100] 
        for e in controversy_map.entries 
        if e.controversy_level in [ControversyLevel.HIGH, ControversyLevel.UNRESOLVED]
    }
    
    for claim in claims:
        if claim.get("is_main_conclusion", False):
            claim_preview = claim.get("claim_text", "")[:100]
            if claim_preview in high_controversy_topics:
                violations.append(claim.get("claim_id", ""))
    
    return len(violations) > 0, violations
