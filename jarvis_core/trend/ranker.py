"""
JARVIS Trend Ranker

ルールベースのトレンドランキング（将来LTRへ移行）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .sources.base import TrendItem

logger = logging.getLogger(__name__)


@dataclass
class RankScore:
    """ランクスコア."""

    novelty: float = 0.0  # 新規性
    credibility: float = 0.0  # 信頼度（一次情報）
    relevance: float = 0.0  # Javisとの関連度
    implementation_cost: float = 0.0  # 導入コスト（低いほど良い）
    risk: float = 0.0  # リスク（低いほど良い）
    evidence_strength: float = 0.0  # エビデンス強度

    @property
    def total(self) -> float:
        """重み付き総合スコア."""
        # デフォルト重み
        weights = {
            "novelty": 0.2,
            "credibility": 0.2,
            "relevance": 0.3,
            "implementation_cost": 0.1,
            "risk": 0.1,
            "evidence_strength": 0.1,
        }

        score = 0.0
        score += weights["novelty"] * self.novelty
        score += weights["credibility"] * self.credibility
        score += weights["relevance"] * self.relevance
        score += weights["implementation_cost"] * (1.0 - self.implementation_cost)
        score += weights["risk"] * (1.0 - self.risk)
        score += weights["evidence_strength"] * self.evidence_strength

        return score


class TrendRanker:
    """トレンドランカー.

    初期: ルールベース
    将来: LightGBM Rankerへ移行
    """

    def __init__(
        self, relevance_keywords: list[str] | None = None, credible_sources: list[str] | None = None
    ):
        """
        初期化.

        Args:
            relevance_keywords: 関連度判定用キーワード
            credible_sources: 信頼できるソースリスト
        """
        self.relevance_keywords = relevance_keywords or [
            "research",
            "meta-analysis",
            "systematic review",
            "machine learning",
            "LLM",
            "RAG",
            "agent",
            "evaluation",
            "benchmark",
            "reproducibility",
        ]
        self.credible_sources = credible_sources or [
            "arxiv",
            "pubmed",
            "nature",
            "science",
            "cell",
        ]

    def rank(self, items: list[TrendItem]) -> list[tuple[TrendItem, RankScore]]:
        """
        アイテムをランキング.

        Args:
            items: TrendItemリスト

        Returns:
            (TrendItem, RankScore) のリスト（スコア降順）
        """
        scored = []

        for item in items:
            score = self._score_item(item)
            scored.append((item, score))

        # 総合スコアで降順ソート
        scored.sort(key=lambda x: x[1].total, reverse=True)

        return scored

    def _score_item(self, item: TrendItem) -> RankScore:
        """単一アイテムをスコアリング."""

        # 新規性（日付ベース）
        novelty = self._calc_novelty(item)

        # 信頼度（ソースベース）
        credibility = self._calc_credibility(item)

        # 関連度（キーワードベース）
        relevance = self._calc_relevance(item)

        # 導入コスト（プレースホルダー）
        implementation_cost = 0.5

        # リスク（プレースホルダー）
        risk = 0.3

        # エビデンス強度（ソースタイプベース）
        evidence_strength = self._calc_evidence_strength(item)

        return RankScore(
            novelty=novelty,
            credibility=credibility,
            relevance=relevance,
            implementation_cost=implementation_cost,
            risk=risk,
            evidence_strength=evidence_strength,
        )

    def _calc_novelty(self, item: TrendItem) -> float:
        """新規性を計算."""
        # プレースホルダー：発行日ベース
        # 7日以内 = 1.0, 30日以内 = 0.5, それ以上 = 0.2
        if not item.published_date:
            return 0.5

        # 簡易実装（実際は日付計算が必要）
        return 0.8

    def _calc_credibility(self, item: TrendItem) -> float:
        """信頼度を計算."""
        source_lower = item.source.lower()

        if any(s in source_lower for s in self.credible_sources):
            return 0.9

        return 0.5

    def _calc_relevance(self, item: TrendItem) -> float:
        """関連度を計算."""
        text = f"{item.title} {item.abstract or ''}".lower()

        matches = sum(1 for kw in self.relevance_keywords if kw.lower() in text)

        return min(1.0, matches / 3.0)

    def _calc_evidence_strength(self, item: TrendItem) -> float:
        """エビデンス強度を計算."""
        # 一次情報（論文）は高い
        source_lower = item.source.lower()

        if "arxiv" in source_lower or "pubmed" in source_lower:
            return 0.9
        elif "github" in source_lower:
            return 0.7
        else:
            return 0.5
