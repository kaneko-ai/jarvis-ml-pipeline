"""
JARVIS Contradiction Detector

4. 矛盾検出: 論文間のclaim矛盾を自動検出
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    """矛盾."""

    claim_a_id: str
    claim_a_text: str
    claim_b_id: str
    claim_b_text: str
    contradiction_type: str  # direct, implicit, contextual
    confidence: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_a_id": self.claim_a_id,
            "claim_a_text": self.claim_a_text,
            "claim_b_id": self.claim_b_id,
            "claim_b_text": self.claim_b_text,
            "contradiction_type": self.contradiction_type,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


class ContradictionDetector:
    """矛盾検出器.

    claim間の矛盾を検出
    - 直接矛盾: 明示的に反対の主張
    - 暗黙矛盾: 論理的に両立しない
    - 文脈矛盾: 特定条件下で矛盾
    """

    # 矛盾パターン（直接）
    NEGATION_PAIRS = [
        ("increase", "decrease"),
        ("enhance", "inhibit"),
        ("activate", "suppress"),
        ("promote", "prevent"),
        ("positive", "negative"),
        ("upregulate", "downregulate"),
        ("high", "low"),
        ("effective", "ineffective"),
    ]

    def __init__(self, embedding_model=None, llm_client=None):
        """初期化."""
        self.embedding_model = embedding_model
        self.llm_client = llm_client

    def detect_contradictions(
        self,
        claims: list[dict[str, Any]],
    ) -> list[Contradiction]:
        """矛盾を検出.

        Args:
            claims: 主張リスト（claim_id, claim_text を含む）

        Returns:
            矛盾リスト
        """
        contradictions = []

        # ペアワイズで比較
        for i, claim_a in enumerate(claims):
            for j, claim_b in enumerate(claims[i + 1 :], i + 1):
                result = self._check_contradiction(claim_a, claim_b)
                if result:
                    contradictions.append(result)

        logger.info(f"Detected {len(contradictions)} contradictions from {len(claims)} claims")
        return contradictions

    def _check_contradiction(
        self,
        claim_a: dict[str, Any],
        claim_b: dict[str, Any],
    ) -> Contradiction | None:
        """2つのclaimの矛盾をチェック."""
        text_a = claim_a.get("claim_text", "").lower()
        text_b = claim_b.get("claim_text", "").lower()

        # 同じトピックについて言及しているかチェック
        if not self._same_topic(text_a, text_b):
            return None

        # 直接矛盾をチェック
        for pos, neg in self.NEGATION_PAIRS:
            if pos in text_a and neg in text_b:
                return Contradiction(
                    claim_a_id=claim_a.get("claim_id", ""),
                    claim_a_text=claim_a.get("claim_text", ""),
                    claim_b_id=claim_b.get("claim_id", ""),
                    claim_b_text=claim_b.get("claim_text", ""),
                    contradiction_type="direct",
                    confidence=0.7,
                    explanation=f"Opposing terms: '{pos}' vs '{neg}'",
                )
            if neg in text_a and pos in text_b:
                return Contradiction(
                    claim_a_id=claim_a.get("claim_id", ""),
                    claim_a_text=claim_a.get("claim_text", ""),
                    claim_b_id=claim_b.get("claim_id", ""),
                    claim_b_text=claim_b.get("claim_text", ""),
                    contradiction_type="direct",
                    confidence=0.7,
                    explanation=f"Opposing terms: '{neg}' vs '{pos}'",
                )

        return None

    def _same_topic(self, text_a: str, text_b: str) -> bool:
        """同じトピックかチェック."""
        # 共通キーワードがあるかチェック
        words_a = set(text_a.split())
        words_b = set(text_b.split())

        # ストップワードを除外
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "of", "in", "to", "and"}
        words_a = words_a - stopwords
        words_b = words_b - stopwords

        # 共通語が2つ以上あれば同じトピック
        common = words_a & words_b
        return len(common) >= 2