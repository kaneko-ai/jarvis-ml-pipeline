"""
JARVIS Evidence Mapper

5. エビデンスマッピング: 図表・文献への参照リンク
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvidenceReference:
    """エビデンス参照."""

    ref_type: str  # figure, table, citation, section
    ref_id: str
    ref_text: str
    location: dict[str, Any]  # page, section, paragraph

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "ref_text": self.ref_text,
            "location": self.location,
        }


@dataclass
class MappedEvidence:
    """マッピング済みエビデンス."""

    claim_id: str
    claim_text: str
    evidence_refs: list[EvidenceReference] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "evidence_refs": [e.to_dict() for e in self.evidence_refs],
            "confidence": self.confidence,
        }


class EvidenceMapper:
    """エビデンスマッパー.

    claimに対して図表・文献参照をマッピング
    """

    # 参照パターン
    FIGURE_PATTERN = r"(?i)(fig(?:ure)?\.?\s*\d+[a-z]?)"
    TABLE_PATTERN = r"(?i)(table\s*\d+[a-z]?)"
    CITATION_PATTERN = r"\[(\d+(?:,\s*\d+)*)\]"
    SECTION_PATTERN = r"(?i)(see\s+(?:section|methods?|results?|discussion))"

    def __init__(self):
        """初期化."""
        pass

    def map_evidence(
        self,
        claims: list[dict[str, Any]],
        full_text: str,
    ) -> list[MappedEvidence]:
        """claimにエビデンスをマッピング.

        Args:
            claims: 主張リスト
            full_text: 全文テキスト

        Returns:
            マッピング済みエビデンスリスト
        """
        results = []

        for claim in claims:
            claim_text = claim.get("claim_text", "")
            source_text = claim.get("source_text", claim_text)

            refs = []

            # 図参照を検出
            figures = re.findall(self.FIGURE_PATTERN, source_text)
            for fig in figures:
                refs.append(
                    EvidenceReference(
                        ref_type="figure",
                        ref_id=fig,
                        ref_text=fig,
                        location=self._find_location(fig, full_text),
                    )
                )

            # 表参照を検出
            tables = re.findall(self.TABLE_PATTERN, source_text)
            for table in tables:
                refs.append(
                    EvidenceReference(
                        ref_type="table",
                        ref_id=table,
                        ref_text=table,
                        location=self._find_location(table, full_text),
                    )
                )

            # 引用参照を検出
            citations = re.findall(self.CITATION_PATTERN, source_text)
            for citation in citations:
                refs.append(
                    EvidenceReference(
                        ref_type="citation",
                        ref_id=citation,
                        ref_text=f"[{citation}]",
                        location={},
                    )
                )

            # セクション参照を検出
            sections = re.findall(self.SECTION_PATTERN, source_text)
            for section in sections:
                refs.append(
                    EvidenceReference(
                        ref_type="section",
                        ref_id=section,
                        ref_text=section,
                        location={},
                    )
                )

            # 信頼度を計算
            confidence = min(1.0, 0.3 + 0.2 * len(refs))

            results.append(
                MappedEvidence(
                    claim_id=claim.get("claim_id", ""),
                    claim_text=claim_text,
                    evidence_refs=refs,
                    confidence=confidence,
                )
            )

        logger.info(f"Mapped evidence for {len(results)} claims")
        return results

    def _find_location(self, ref: str, full_text: str) -> dict[str, Any]:
        """参照の位置を特定."""
        match = re.search(re.escape(ref), full_text, re.IGNORECASE)
        if match:
            # 文字位置から行番号を計算
            lines_before = full_text[: match.start()].count("\n")
            return {
                "line": lines_before + 1,
                "offset": match.start(),
            }
        return {}
