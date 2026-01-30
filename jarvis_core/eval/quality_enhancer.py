"""ITER-04: Claim/Evidence品質 (Quality Enhancement).

主張と根拠の品質向上。
- 信頼度再計算
- 重複除去
- 品質スコアリング
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class QualityScore:
    """品質スコア."""

    overall: float = 0.0
    specificity: float = 0.0
    verifiability: float = 0.0
    uniqueness: float = 0.0
    completeness: float = 0.0

    def to_dict(self) -> dict:
        return {
            "overall": self.overall,
            "specificity": self.specificity,
            "verifiability": self.verifiability,
            "uniqueness": self.uniqueness,
            "completeness": self.completeness,
        }


class ClaimQualityEnhancer:
    """主張品質向上器."""

    def __init__(self, min_quality: float = 0.5):
        self.min_quality = min_quality
        self._seen_hashes: set[str] = set()

    def enhance(self, claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """主張リストを品質向上."""
        enhanced = []
        self._seen_hashes.clear()

        for claim in claims:
            # 重複チェック
            claim_hash = self._hash_claim(claim)
            if claim_hash in self._seen_hashes:
                continue
            self._seen_hashes.add(claim_hash)

            # 品質スコア計算
            quality = self._calculate_quality(claim)

            # 最低品質以上のみ保持
            if quality.overall >= self.min_quality:
                claim["quality_score"] = quality.to_dict()
                claim["confidence"] = quality.overall
                enhanced.append(claim)

        # スコア順にソート
        enhanced.sort(key=lambda c: c.get("quality_score", {}).get("overall", 0), reverse=True)

        return enhanced

    def _hash_claim(self, claim: dict[str, Any]) -> str:
        """主張のハッシュを生成."""
        text = claim.get("claim_text", "").lower()
        # 正規化
        text = re.sub(r"\s+", " ", text).strip()
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _calculate_quality(self, claim: dict[str, Any]) -> QualityScore:
        """品質スコアを計算."""
        text = claim.get("claim_text", "")

        score = QualityScore()

        # 特異性: 具体的な数値/固有名詞があるか
        score.specificity = self._calculate_specificity(text)

        # 検証可能性: 検証可能な形式か
        score.verifiability = self._calculate_verifiability(text)

        # 一意性: 一般的すぎないか
        score.uniqueness = self._calculate_uniqueness(text)

        # 完全性: 主語述語があるか
        score.completeness = self._calculate_completeness(text)

        # 総合スコア
        score.overall = (
            score.specificity * 0.3
            + score.verifiability * 0.3
            + score.uniqueness * 0.2
            + score.completeness * 0.2
        )

        return score

    def _calculate_specificity(self, text: str) -> float:
        """特異性スコアを計算."""
        score = 0.5

        # 数値がある
        if re.search(r"\d+(?:\.\d+)?%?", text):
            score += 0.2

        # 遺伝子/タンパク質名
        if re.search(r"\b[A-Z][A-Z0-9]{1,5}\b", text):
            score += 0.15

        # 具体的な単位
        if re.search(r"\b(?:mg|μg|mL|μM|nM|kDa|IC50|EC50)\b", text, re.IGNORECASE):
            score += 0.15

        return min(1.0, score)

    def _calculate_verifiability(self, text: str) -> float:
        """検証可能性スコアを計算."""
        score = 0.5

        # 結果を示す動詞
        if re.search(r"\b(?:showed?|demonstrated?|indicated?|revealed?|found)\b", text.lower()):
            score += 0.2

        # 統計的有意性
        if re.search(r"\bp\s*[<>=]\s*\d", text.lower()):
            score += 0.2

        # 曖昧な表現
        if re.search(r"\b(?:may|might|could|possibly|potentially)\b", text.lower()):
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _calculate_uniqueness(self, text: str) -> float:
        """一意性スコアを計算."""
        score = 0.7

        # 一般的すぎる表現
        generic = ["is important", "plays a role", "is involved", "is associated"]
        for g in generic:
            if g in text.lower():
                score -= 0.15

        # 短すぎる
        if len(text) < 50:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _calculate_completeness(self, text: str) -> float:
        """完全性スコアを計算."""
        score = 0.5

        # 主語がありそう
        if text[0].isupper():
            score += 0.1

        # 適切な長さ
        if 50 <= len(text) <= 300:
            score += 0.2

        # 文として完結（ピリオドで終わる）
        if text.rstrip().endswith("."):
            score += 0.2

        return min(1.0, score)


class EvidenceQualityEnhancer:
    """根拠品質向上器."""

    def __init__(self, min_quality: float = 0.5):
        self.min_quality = min_quality

    def enhance(self, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """根拠リストを品質向上."""
        enhanced = []

        for ev in evidence:
            quality = self._calculate_quality(ev)

            if quality.overall >= self.min_quality:
                ev["quality_score"] = quality.to_dict()
                enhanced.append(ev)

        return enhanced

    def _calculate_quality(self, ev: dict[str, Any]) -> QualityScore:
        """品質スコアを計算."""
        text = ev.get("evidence_text", "")
        locator = ev.get("locator", {})

        score = QualityScore()

        # Locatorの存在
        if locator and locator.get("section"):
            score.completeness = 0.8
            if locator.get("paragraph"):
                score.completeness = 1.0
        else:
            score.completeness = 0.3

        # テキストの質
        score.specificity = 0.5
        if len(text) > 50:
            score.specificity += 0.2
        if re.search(r"\d+", text):
            score.specificity += 0.15

        score.verifiability = 0.6
        score.uniqueness = 0.7

        score.overall = (
            score.specificity * 0.3
            + score.completeness * 0.4
            + score.verifiability * 0.2
            + score.uniqueness * 0.1
        )

        return score


def enhance_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """便利関数: 主張を品質向上."""
    enhancer = ClaimQualityEnhancer()
    return enhancer.enhance(claims)


def enhance_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """便利関数: 根拠を品質向上."""
    enhancer = EvidenceQualityEnhancer()
    return enhancer.enhance(evidence)