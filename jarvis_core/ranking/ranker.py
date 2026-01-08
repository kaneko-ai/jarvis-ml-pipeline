"""Ranker (P-06).

論文・主張のランキング。
重み設定可能な複合スコアリング。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RankingWeights:
    """ランキングの重み設定."""
    relevance: float = 0.4
    evidence: float = 0.3
    recency: float = 0.15
    methodology: float = 0.15

    def to_dict(self) -> dict:
        return {
            "relevance": self.relevance,
            "evidence": self.evidence,
            "recency": self.recency,
            "methodology": self.methodology,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RankingWeights:
        return cls(
            relevance=d.get("relevance", 0.4),
            evidence=d.get("evidence", 0.3),
            recency=d.get("recency", 0.15),
            methodology=d.get("methodology", 0.15),
        )

    @classmethod
    def load(cls, filepath: Path) -> RankingWeights:
        """YAMLファイルから読み込み."""
        try:
            import yaml
            with open(filepath, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data)
        except:
            return cls()


@dataclass
class RankedItem:
    """ランク付けされたアイテム."""
    item_id: str
    item_type: str  # paper, claim
    score: float
    rank: int
    factors: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "score": self.score,
            "rank": self.rank,
            "factors": self.factors,
            "metadata": self.metadata,
        }


@dataclass
class RankingResult:
    """ランキング結果."""
    items: list[RankedItem] = field(default_factory=list)
    weights_used: RankingWeights | None = None

    def to_dict(self) -> dict:
        return {
            "items": [i.to_dict() for i in self.items],
            "weights_used": self.weights_used.to_dict() if self.weights_used else None,
        }


class Ranker:
    """論文・主張ランカー.
    
    複合スコアに基づいてアイテムをランク付け。
    """

    def __init__(
        self,
        weights: RankingWeights | None = None,
        current_year: int = 2024,
    ):
        self.weights = weights or RankingWeights()
        self.current_year = current_year

    def rank_papers(
        self,
        papers: list[dict[str, Any]],
        query: str = "",
        evidence_counts: dict[str, int] | None = None,
    ) -> RankingResult:
        """論文をランク付け.
        
        Args:
            papers: 論文リスト [{paper_id, title, year, abstract, ...}]
            query: 検索クエリ（関連度計算用）
            evidence_counts: paper_id -> 根拠数のマップ
            
        Returns:
            RankingResult
        """
        evidence_counts = evidence_counts or {}
        ranked = []

        for paper in papers:
            paper_id = paper.get("paper_id", "")

            # 各因子を計算
            factors = {
                "relevance": self._compute_relevance(paper, query),
                "evidence": self._compute_evidence_factor(paper_id, evidence_counts),
                "recency": self._compute_recency(paper),
                "methodology": self._compute_methodology(paper),
            }

            # 重み付き総合スコア
            score = (
                factors["relevance"] * self.weights.relevance +
                factors["evidence"] * self.weights.evidence +
                factors["recency"] * self.weights.recency +
                factors["methodology"] * self.weights.methodology
            ) * 100  # 0-100スケール

            ranked.append(RankedItem(
                item_id=paper_id,
                item_type="paper",
                score=score,
                rank=0,  # 後で設定
                factors=factors,
                metadata={
                    "title": paper.get("title", ""),
                    "year": paper.get("year", 0),
                },
            ))

        # スコアでソートしてランク付け
        ranked.sort(key=lambda x: x.score, reverse=True)
        for i, item in enumerate(ranked):
            item.rank = i + 1

        return RankingResult(items=ranked, weights_used=self.weights)

    def rank_claims(
        self,
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> RankingResult:
        """主張をランク付け.
        
        Args:
            claims: 主張リスト
            evidence: 根拠リスト
            
        Returns:
            RankingResult
        """
        # 主張ごとの根拠カウント
        evidence_by_claim = {}
        for ev in evidence:
            claim_id = ev.get("claim_id", "")
            evidence_by_claim[claim_id] = evidence_by_claim.get(claim_id, 0) + 1

        ranked = []

        for claim in claims:
            claim_id = claim.get("claim_id", "")

            # 因子計算
            ev_count = evidence_by_claim.get(claim_id, 0)
            confidence = claim.get("confidence", 0.5)
            claim_type = claim.get("claim_type", "fact")

            factors = {
                "evidence": min(1.0, ev_count / 3),  # 3根拠で最大
                "confidence": confidence,
                "type_weight": self._claim_type_weight(claim_type),
            }

            score = (
                factors["evidence"] * 0.5 +
                factors["confidence"] * 0.3 +
                factors["type_weight"] * 0.2
            ) * 100

            ranked.append(RankedItem(
                item_id=claim_id,
                item_type="claim",
                score=score,
                rank=0,
                factors=factors,
                metadata={
                    "claim_text": claim.get("claim_text", "")[:100],
                    "claim_type": claim_type,
                },
            ))

        # ソートとランク付け
        ranked.sort(key=lambda x: x.score, reverse=True)
        for i, item in enumerate(ranked):
            item.rank = i + 1

        return RankingResult(items=ranked, weights_used=self.weights)

    def _compute_relevance(self, paper: dict[str, Any], query: str) -> float:
        """関連度を計算."""
        if not query:
            return 0.5

        query_lower = query.lower()
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()

        # キーワードマッチ
        import re
        keywords = re.findall(r'\b[a-z]{3,}\b', query_lower)
        if not keywords:
            return 0.5

        title_matches = sum(1 for kw in keywords if kw in title)
        abstract_matches = sum(1 for kw in keywords if kw in abstract)

        title_score = title_matches / len(keywords)
        abstract_score = abstract_matches / len(keywords) * 0.5

        return min(1.0, title_score + abstract_score)

    def _compute_evidence_factor(self, paper_id: str, evidence_counts: dict[str, int]) -> float:
        """根拠因子を計算."""
        count = evidence_counts.get(paper_id, 0)
        return min(1.0, count / 5)  # 5根拠で最大

    def _compute_recency(self, paper: dict[str, Any]) -> float:
        """新しさ因子を計算."""
        year = paper.get("year", 2020)
        age = self.current_year - year

        if age <= 0:
            return 1.0
        elif age <= 2:
            return 0.9
        elif age <= 5:
            return 0.7
        elif age <= 10:
            return 0.5
        else:
            return 0.3

    def _compute_methodology(self, paper: dict[str, Any]) -> float:
        """方法論スコアを計算（簡易版）."""
        # 本番ではより詳細な評価が必要
        abstract = paper.get("abstract", "").lower()

        indicators = ["randomized", "controlled", "clinical trial", "meta-analysis", "systematic review"]
        score = 0.5

        for ind in indicators:
            if ind in abstract:
                score += 0.1

        return min(1.0, score)

    def _claim_type_weight(self, claim_type: str) -> float:
        """主張タイプの重み."""
        weights = {
            "result": 1.0,
            "conclusion": 0.9,
            "fact": 0.8,
            "methodology": 0.6,
            "hypothesis": 0.4,
        }
        return weights.get(claim_type, 0.5)


def rank_papers(
    papers: list[dict[str, Any]],
    query: str = "",
    weights: RankingWeights | None = None,
) -> RankingResult:
    """便利関数: 論文をランク付け."""
    ranker = Ranker(weights=weights)
    return ranker.rank_papers(papers, query)
