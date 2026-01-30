"""
JARVIS Evidence Validator - スパン単位検証ゲート

Claimのevidenceが正しいスパンを参照しているか機械判定。
- doc_id/section/chunk_id/start/end の存在確認
- start/end が原文範囲内であること
- claim_text と evidence_text の最低限の整合
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jarvis_core.contracts.types import Claim, EvidenceLink, Paper


@dataclass
class ValidationResult:
    """検証結果."""

    valid: bool
    reasons: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "reasons": self.reasons, "warnings": self.warnings}


class EvidenceValidator:
    """
    Evidence Link Validator.

    スパン単位で根拠の妥当性を検証。
    """

    # 数値パターン
    NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")

    # 重要エンティティパターン（分子名、疾患名など）
    ENTITY_PATTERNS = [
        re.compile(r"CD\d+", re.IGNORECASE),  # CD73, CD39など
        re.compile(r"[A-Z]{2,}(?:-\d+)?", re.IGNORECASE),  # TNF-α, IL-6など
        re.compile(r"(?:cancer|tumor|carcinoma|lymphoma|melanoma)", re.IGNORECASE),
    ]

    def __init__(self, doc_store: dict[str, Paper] | None = None):
        """
        初期化.

        Args:
            doc_store: doc_id -> Paper のマッピング
        """
        self.doc_store = doc_store or {}

    def validate_evidence_link(
        self, claim: Claim, doc_store: dict[str, Paper] | None = None
    ) -> ValidationResult:
        """
        Claimの全evidenceを検証.

        Args:
            claim: 検証対象のClaim
            doc_store: ドキュメントストア（省略時は初期化時の値）

        Returns:
            ValidationResult
        """
        store = doc_store or self.doc_store
        reasons = []
        warnings = []

        if not claim.evidence:
            return ValidationResult(valid=False, reasons=["No evidence links found"], warnings=[])

        for i, ev in enumerate(claim.evidence):
            ev_result = self._validate_single_link(ev, claim.claim_text, store, i)
            reasons.extend(ev_result[0])
            warnings.extend(ev_result[1])

        # 全エビデンスが有効ならvalid
        valid = len(reasons) == 0

        return ValidationResult(valid=valid, reasons=reasons, warnings=warnings)

    def _validate_single_link(
        self, ev: EvidenceLink, claim_text: str, store: dict[str, Paper], index: int
    ) -> tuple[list[str], list[str]]:
        """単一のEvidenceLinkを検証."""
        reasons = []
        warnings = []
        prefix = f"[Evidence {index}]"

        # 1. 必須フィールドチェック
        if not ev.doc_id:
            reasons.append(f"{prefix} Missing doc_id")
        if not ev.section:
            reasons.append(f"{prefix} Missing section")
        if not ev.chunk_id:
            reasons.append(f"{prefix} Missing chunk_id")

        # 2. スパン範囲チェック
        if ev.start < 0:
            reasons.append(f"{prefix} Invalid start position: {ev.start}")
        if ev.end < ev.start:
            reasons.append(f"{prefix} Invalid span: end ({ev.end}) < start ({ev.start})")

        # 3. ドキュメント存在チェック
        if store and ev.doc_id not in store and ev.doc_id != "internal":
            warnings.append(f"{prefix} Document not in store: {ev.doc_id}")

        # 4. スパンが原文範囲内かチェック
        if store and ev.doc_id in store:
            paper = store[ev.doc_id]
            text = self._get_section_text(paper, ev.section)
            if text and ev.end > len(text):
                reasons.append(
                    f"{prefix} Span exceeds document length: " f"end={ev.end}, doc_len={len(text)}"
                )

        # 5. 整合性チェック（数値・エンティティ）
        if ev.text:
            coherence_result = self._check_coherence(claim_text, ev.text)
            warnings.extend([f"{prefix} {w}" for w in coherence_result])

        return reasons, warnings

    def _get_section_text(self, paper: Paper, section: str) -> str | None:
        """論文からセクションテキストを取得."""
        if section == "title":
            return paper.title
        elif section == "abstract":
            return paper.abstract
        elif section in paper.sections:
            return paper.sections[section]
        elif section in paper.chunks:
            return paper.chunks[section]
        return None

    def _check_coherence(self, claim_text: str, evidence_text: str) -> list[str]:
        """
        Claimとevidenceの整合性をチェック.

        - 数値を含む主張ならevidenceに同数値が存在
        - 分子名/疾患名の一致
        """
        warnings = []

        # 数値チェック
        claim_numbers = set(self.NUMBER_PATTERN.findall(claim_text))
        evidence_numbers = set(self.NUMBER_PATTERN.findall(evidence_text))

        # 重要な数値（2桁以上）が一致しない場合
        significant_claim_nums = {n for n in claim_numbers if len(n) >= 2}
        if significant_claim_nums:
            missing = significant_claim_nums - evidence_numbers
            if missing and len(missing) == len(significant_claim_nums):
                warnings.append(
                    f"Numeric mismatch: claim contains {significant_claim_nums}, "
                    f"evidence contains {evidence_numbers}"
                )

        # エンティティチェック
        claim_entities = self._extract_entities(claim_text)
        evidence_entities = self._extract_entities(evidence_text)

        if claim_entities:
            overlap = claim_entities & evidence_entities
            if not overlap and len(claim_entities) <= 3:
                warnings.append(
                    f"Entity mismatch: claim entities {claim_entities} " f"not found in evidence"
                )

        return warnings

    def _extract_entities(self, text: str) -> set:
        """テキストからエンティティを抽出."""
        entities = set()
        for pattern in self.ENTITY_PATTERNS:
            matches = pattern.findall(text)
            entities.update(m.upper() for m in matches)
        return entities

    def validate_all_claims(
        self, claims: list[Claim], doc_store: dict[str, Paper] | None = None
    ) -> dict[str, Any]:
        """
        全Claimを検証.

        Returns:
            {
                "total": 10,
                "valid": 8,
                "invalid": 2,
                "rate": 0.8,
                "details": [...]
            }
        """
        store = doc_store or self.doc_store
        results = []
        valid_count = 0

        for claim in claims:
            result = self.validate_evidence_link(claim, store)
            results.append(
                {
                    "claim_id": claim.claim_id,
                    "claim_text": claim.claim_text[:100],
                    "result": result.to_dict(),
                }
            )
            if result.valid:
                valid_count += 1

        total = len(claims)
        rate = valid_count / total if total > 0 else 0.0

        return {
            "total": total,
            "valid": valid_count,
            "invalid": total - valid_count,
            "rate": rate,
            "details": results,
        }


def get_evidence_validator(doc_store: dict[str, Paper] | None = None) -> EvidenceValidator:
    """EvidenceValidatorを取得."""
    return EvidenceValidator(doc_store)


def validate_evidence_link(claim: Claim, doc_store: dict[str, Paper]) -> ValidationResult:
    """
    Claimのevidenceを検証（便利関数）.

    Args:
        claim: 検証対象のClaim
        doc_store: ドキュメントストア

    Returns:
        ValidationResult
    """
    validator = EvidenceValidator(doc_store)
    return validator.validate_evidence_link(claim, doc_store)