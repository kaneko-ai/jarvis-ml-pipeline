"""
JARVIS Ranking Module

Phase C: LightGBM Ranking + Score Explanation

特徴量:
- recency: 年度
- evidence_count: 根拠数
- domain_match: ドメイン一致度
- reproducibility: 再現性フラグ

説明可能性:
- 各論文の順位理由をreport.mdに出力
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """特徴量ベクトル."""
    paper_id: str
    recency: float = 0.0
    evidence_count: float = 0.0
    domain_match: float = 0.0
    reproducibility: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "recency": self.recency,
            "evidence_count": self.evidence_count,
            "domain_match": self.domain_match,
            "reproducibility": self.reproducibility,
        }
    
    def weighted_score(self, weights: Dict[str, float]) -> float:
        """重み付きスコア."""
        score = 0.0
        for k, v in self.to_dict().items():
            score += v * weights.get(k, 0.0)
        return score


@dataclass
class RankExplanation:
    """順位の説明."""
    paper_id: str
    rank: int
    score: float
    top_factors: List[Tuple[str, float]]  # (feature_name, contribution)
    
    def to_markdown(self) -> str:
        """Markdown形式で出力."""
        factors = ", ".join([f"{k}={v:.2f}" for k, v in self.top_factors[:3]])
        return f"#{self.rank}: score={self.score:.3f} ({factors})"


class PaperRanker:
    """論文ランカー.
    
    Phase C: 特徴量ベースのランキング
    - LightGBMは将来実装（現在は重み付き和）
    - 説明可能性を重視
    """
    
    DEFAULT_WEIGHTS = {
        "recency": 0.3,
        "evidence_count": 0.4,
        "domain_match": 0.2,
        "reproducibility": 0.1,
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """初期化."""
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    def rank(
        self,
        features: List[FeatureVector],
    ) -> List[RankExplanation]:
        """ランキングを実行.
        
        Args:
            features: 特徴量リスト
        
        Returns:
            順位付き説明リスト
        """
        # スコア計算
        scored = []
        for fv in features:
            score = fv.weighted_score(self.weights)
            contributions = [
                (k, v * self.weights.get(k, 0.0))
                for k, v in fv.to_dict().items()
            ]
            contributions.sort(key=lambda x: -x[1])
            scored.append((fv.paper_id, score, contributions))
        
        # スコア降順でソート
        scored.sort(key=lambda x: -x[1])
        
        # 説明を生成
        explanations = []
        for rank, (paper_id, score, contribs) in enumerate(scored, 1):
            explanations.append(RankExplanation(
                paper_id=paper_id,
                rank=rank,
                score=score,
                top_factors=contribs,
            ))
        
        return explanations
    
    def generate_report_section(
        self,
        explanations: List[RankExplanation],
        top_n: int = 3,
    ) -> str:
        """report.md用のセクションを生成.
        
        Args:
            explanations: 順位説明リスト
            top_n: 上位N件
        
        Returns:
            Markdown文字列
        """
        lines = [
            "## Ranking Explanation",
            "",
            "| Rank | Paper ID | Score | Top Factors |",
            "|------|----------|-------|-------------|",
        ]
        
        for exp in explanations[:top_n]:
            factors = ", ".join([f"{k}={v:.2f}" for k, v in exp.top_factors[:2]])
            lines.append(f"| {exp.rank} | {exp.paper_id} | {exp.score:.3f} | {factors} |")
        
        lines.append("")
        lines.append("**Note**: Ranking is based on weighted features. "
                     "Higher evidence_count and recency contribute more to the score.")
        
        return "\n".join(lines)


# ============================================================
# Budget Control (Test-time Scaling)
# ============================================================

@dataclass
class InferenceBudget:
    """推論バジェット.
    
    Phase C: test-time scaling
    - low: abstract only, top_k=1
    - medium: abstract + 1st paragraph, top_k=3
    - high: full text, top_k=5
    """
    level: str  # low, medium, high
    top_k: int
    use_fulltext: bool
    
    @classmethod
    def from_level(cls, level: str) -> "InferenceBudget":
        """レベルから生成."""
        configs = {
            "low": {"top_k": 1, "use_fulltext": False},
            "medium": {"top_k": 3, "use_fulltext": False},
            "high": {"top_k": 5, "use_fulltext": True},
        }
        cfg = configs.get(level, configs["medium"])
        return cls(
            level=level,
            top_k=cfg["top_k"],
            use_fulltext=cfg["use_fulltext"],
        )


class BudgetController:
    """バジェットコントローラー.
    
    cheap→expensive の制御
    """
    
    def __init__(self, budget: InferenceBudget):
        """初期化."""
        self.budget = budget
        self.cheap_count = 0
        self.expensive_count = 0
    
    def should_use_expensive(self, rank: int) -> bool:
        """expensive passを使うべきか."""
        if rank <= self.budget.top_k:
            self.expensive_count += 1
            return True
        self.cheap_count += 1
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """統計を取得."""
        return {
            "budget_level": self.budget.level,
            "top_k": self.budget.top_k,
            "use_fulltext": self.budget.use_fulltext,
            "cheap_passes": self.cheap_count,
            "expensive_passes": self.expensive_count,
        }
