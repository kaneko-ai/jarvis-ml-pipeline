"""ITER-05: ランキング説明可能化 (Explainable Ranking).

ランキングの根拠を説明可能に。
- 要因分解
- テキスト説明生成
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RankingExplanation:
    """ランキング説明."""
    item_id: str
    rank: int
    score: float
    factors: Dict[str, float] = field(default_factory=dict)
    explanation_text: str = ""
    contributing_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "rank": self.rank,
            "score": self.score,
            "factors": self.factors,
            "explanation": self.explanation_text,
            "contributing_factors": self.contributing_factors,
        }


class ExplainableRanker:
    """説明可能ランカー.
    
    ランキングの根拠を人間が理解できる形で説明。
    """
    
    FACTOR_DESCRIPTIONS = {
        "relevance": "クエリとの関連度",
        "evidence": "根拠の強さ",
        "recency": "論文の新しさ",
        "methodology": "方法論の質",
        "confidence": "主張の信頼度",
        "type_weight": "主張タイプの重み",
    }
    
    def __init__(self, top_factors: int = 3):
        self.top_factors = top_factors
    
    def explain(
        self,
        item_id: str,
        rank: int,
        score: float,
        factors: Dict[str, float],
    ) -> RankingExplanation:
        """単一アイテムのランキングを説明."""
        # 上位要因を抽出
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        top = sorted_factors[:self.top_factors]
        
        # 貢献要因リスト
        contributing = [
            f"{self.FACTOR_DESCRIPTIONS.get(f, f)}: {v:.2f}"
            for f, v in top
        ]
        
        # テキスト説明生成
        explanation = self._generate_explanation(rank, score, top, factors)
        
        return RankingExplanation(
            item_id=item_id,
            rank=rank,
            score=score,
            factors=factors,
            explanation_text=explanation,
            contributing_factors=contributing,
        )
    
    def explain_batch(
        self,
        ranked_items: List[Dict[str, Any]],
    ) -> List[RankingExplanation]:
        """バッチでランキングを説明."""
        explanations = []
        
        for item in ranked_items:
            exp = self.explain(
                item_id=item.get("item_id", ""),
                rank=item.get("rank", 0),
                score=item.get("score", 0),
                factors=item.get("factors", {}),
            )
            explanations.append(exp)
        
        return explanations
    
    def _generate_explanation(
        self,
        rank: int,
        score: float,
        top_factors: List[tuple],
        all_factors: Dict[str, float],
    ) -> str:
        """テキスト説明を生成."""
        lines = []
        
        # ランク説明
        if rank <= 3:
            lines.append(f"上位{rank}位（スコア: {score:.1f}/100）")
        elif rank <= 10:
            lines.append(f"上位10以内（{rank}位、スコア: {score:.1f}/100）")
        else:
            lines.append(f"{rank}位（スコア: {score:.1f}/100）")
        
        # 主要因説明
        if top_factors:
            main_factor, main_value = top_factors[0]
            main_desc = self.FACTOR_DESCRIPTIONS.get(main_factor, main_factor)
            
            if main_value > 0.8:
                lines.append(f"特に{main_desc}が高い（{main_value:.2f}）。")
            elif main_value > 0.5:
                lines.append(f"{main_desc}が比較的高い（{main_value:.2f}）。")
        
        # 改善点
        low_factors = [
            (f, v) for f, v in all_factors.items()
            if v < 0.5 and f in self.FACTOR_DESCRIPTIONS
        ]
        if low_factors:
            low_f, low_v = min(low_factors, key=lambda x: x[1])
            low_desc = self.FACTOR_DESCRIPTIONS.get(low_f, low_f)
            lines.append(f"{low_desc}を改善する余地あり（{low_v:.2f}）。")
        
        return " ".join(lines)
    
    def generate_summary(
        self,
        explanations: List[RankingExplanation],
    ) -> str:
        """ランキング全体のサマリーを生成."""
        if not explanations:
            return "ランキング結果がありません。"
        
        lines = [f"## ランキングサマリー（{len(explanations)}件）\n"]
        
        # 上位3件
        lines.append("### 上位3件")
        for exp in explanations[:3]:
            lines.append(f"- **{exp.rank}位**: {exp.item_id}")
            lines.append(f"  - {exp.explanation_text}")
        
        # 共通パターン
        all_factors = {}
        for exp in explanations:
            for f, v in exp.factors.items():
                if f not in all_factors:
                    all_factors[f] = []
                all_factors[f].append(v)
        
        avg_factors = {
            f: sum(v) / len(v)
            for f, v in all_factors.items()
        }
        
        lines.append("\n### 全体傾向")
        for f, avg in sorted(avg_factors.items(), key=lambda x: x[1], reverse=True)[:3]:
            desc = self.FACTOR_DESCRIPTIONS.get(f, f)
            lines.append(f"- {desc}: 平均 {avg:.2f}")
        
        return "\n".join(lines)


def explain_ranking(ranked_items: List[Dict[str, Any]]) -> List[RankingExplanation]:
    """便利関数: ランキングを説明."""
    explainer = ExplainableRanker()
    return explainer.explain_batch(ranked_items)
