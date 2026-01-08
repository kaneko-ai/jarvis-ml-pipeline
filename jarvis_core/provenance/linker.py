"""
JARVIS Provenance Module - 根拠付けユーティリティ

全ての出力に evidence_links を強制する。
根拠がない出力は禁止（捏造禁止）。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from jarvis_core.contracts.types import Claim, EvidenceLink


class ProvenanceError(Exception):
    """根拠付けエラー."""
    pass


@dataclass
class ChunkInfo:
    """チャンク情報."""
    doc_id: str
    section: str
    chunk_id: str
    text: str
    start: int
    end: int


class ProvenanceLinker:
    """
    根拠付けユーティリティ.
    
    文章出力に evidence_links を付与する。
    根拠がない場合は「不明」と明示し、スコアを下げる。
    """

    def __init__(self, strict: bool = True, min_confidence: float = 0.5):
        """
        Args:
            strict: 厳密モード（根拠なしを禁止）
            min_confidence: 最小信頼度閾値
        """
        self.strict = strict
        self.min_confidence = min_confidence
        self.chunks: dict[str, ChunkInfo] = {}

    def register_chunk(self, doc_id: str, section: str,
                       chunk_id: str, text: str,
                       start: int = 0, end: int | None = None) -> None:
        """
        チャンクを登録する.
        
        Args:
            doc_id: ドキュメントID
            section: セクション名
            chunk_id: チャンクID
            text: テキスト
            start: 開始位置
            end: 終了位置
        """
        end = end or (start + len(text))
        self.chunks[chunk_id] = ChunkInfo(
            doc_id=doc_id,
            section=section,
            chunk_id=chunk_id,
            text=text,
            start=start,
            end=end
        )

    def register_chunks_from_document(self, doc_id: str,
                                       sections: dict[str, str],
                                       chunk_size: int = 500,
                                       overlap: int = 50) -> list[str]:
        """
        ドキュメントからチャンクを自動登録.
        
        Args:
            doc_id: ドキュメントID
            sections: セクション名 -> テキスト
            chunk_size: チャンクサイズ
            overlap: オーバーラップ
        
        Returns:
            登録されたchunk_idのリスト
        """
        chunk_ids = []

        for section, text in sections.items():
            pos = 0
            chunk_num = 0

            while pos < len(text):
                end = min(pos + chunk_size, len(text))
                chunk_text = text[pos:end]

                chunk_id = self._generate_chunk_id(doc_id, section, chunk_num)
                self.register_chunk(doc_id, section, chunk_id, chunk_text, pos, end)
                chunk_ids.append(chunk_id)

                pos += chunk_size - overlap
                chunk_num += 1

        return chunk_ids

    def _generate_chunk_id(self, doc_id: str, section: str, num: int) -> str:
        """チャンクIDを生成."""
        content = f"{doc_id}:{section}:{num}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def find_evidence(self, claim_text: str,
                      threshold: float = 0.5) -> list[EvidenceLink]:
        """
        主張に対する根拠を検索.
        
        Args:
            claim_text: 主張テキスト
            threshold: 類似度閾値
        
        Returns:
            EvidenceLinkのリスト
        """
        evidence = []

        # Simple keyword matching (replace with embedding similarity in production)
        claim_words = set(self._tokenize(claim_text))

        for chunk_id, chunk in self.chunks.items():
            chunk_words = set(self._tokenize(chunk.text))

            if not chunk_words:
                continue

            # Jaccard similarity
            intersection = claim_words & chunk_words
            union = claim_words | chunk_words
            similarity = len(intersection) / len(union) if union else 0

            if similarity >= threshold:
                # Find exact span if possible
                start, end = self._find_span(claim_text, chunk.text)

                evidence.append(EvidenceLink(
                    doc_id=chunk.doc_id,
                    section=chunk.section,
                    chunk_id=chunk_id,
                    start=start,
                    end=end,
                    confidence=similarity,
                    text=chunk.text[start:end] if start >= 0 else None
                ))

        # Sort by confidence
        evidence.sort(key=lambda e: e.confidence, reverse=True)

        return evidence

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in text.split() if len(w) > 2]

    def _find_span(self, claim: str, chunk: str) -> tuple[int, int]:
        """Find the best matching span in chunk for claim."""
        claim_lower = claim.lower()
        chunk_lower = chunk.lower()

        # Try exact substring match
        idx = chunk_lower.find(claim_lower)
        if idx >= 0:
            return idx, idx + len(claim)

        # Try partial match (first sentence)
        sentences = re.split(r'[.!?]', claim)
        if sentences:
            first = sentences[0].strip().lower()
            idx = chunk_lower.find(first)
            if idx >= 0:
                return idx, idx + len(first)

        # Return full chunk if no match
        return 0, len(chunk)

    def create_claim(self, claim_id: str, claim_text: str,
                     claim_type: str = "fact",
                     auto_link: bool = True) -> Claim:
        """
        根拠付き主張を作成.
        
        Args:
            claim_id: 主張ID
            claim_text: 主張テキスト
            claim_type: 主張タイプ
            auto_link: 自動で根拠を検索するか
        
        Returns:
            Claim with evidence_links
        """
        evidence = []

        if auto_link:
            evidence = self.find_evidence(claim_text)

        confidence = 0.0
        if evidence:
            confidence = sum(e.confidence for e in evidence) / len(evidence)

        claim = Claim(
            claim_id=claim_id,
            claim_text=claim_text,
            evidence=evidence,
            claim_type=claim_type,
            confidence=confidence
        )

        # Strict mode: reject claims without evidence
        if self.strict and not evidence:
            claim.claim_type = "hypothesis"  # Downgrade to hypothesis
            claim.confidence = 0.0

        return claim

    def validate_claims(self, claims: list[Claim],
                        min_rate: float = 0.95) -> tuple[bool, float, list[str]]:
        """
        主張群の根拠付け率を検証.
        
        Args:
            claims: 主張リスト
            min_rate: 最小根拠付け率
        
        Returns:
            (合格フラグ, 実際の率, 警告リスト)
        """
        if not claims:
            return False, 0.0, ["No claims to validate"]

        with_evidence = [c for c in claims if c.has_evidence()]
        rate = len(with_evidence) / len(claims)

        warnings = []
        for c in claims:
            if not c.has_evidence():
                warnings.append(f"Claim {c.claim_id} has no evidence")

        passed = rate >= min_rate

        return passed, rate, warnings

    def attach_evidence(self, claim: Claim,
                        evidence_links: list[EvidenceLink]) -> Claim:
        """
        既存の主張に根拠を追加.
        """
        claim.evidence.extend(evidence_links)
        if claim.evidence:
            claim.confidence = sum(e.confidence for e in claim.evidence) / len(claim.evidence)
        return claim

    def get_missing_evidence_claims(self, claims: list[Claim]) -> list[Claim]:
        """根拠のない主張を取得."""
        return [c for c in claims if not c.has_evidence()]


class ProvenanceValidator:
    """
    根拠検証器.
    
    全出力が根拠付けされているか検証する。
    """

    def __init__(self, min_rate: float = 0.95,
                 reject_assertions_without_evidence: bool = True):
        self.min_rate = min_rate
        self.reject_assertions = reject_assertions_without_evidence

    def validate(self, claims: list[Claim]) -> dict[str, Any]:
        """
        根拠付けを検証.
        
        Returns:
            検証結果（passed, rate, issues, etc.）
        """
        if not claims:
            return {
                "passed": False,
                "rate": 0.0,
                "issues": ["No claims to validate"],
                "claims_total": 0,
                "claims_with_evidence": 0
            }

        with_evidence = [c for c in claims if c.has_evidence()]
        rate = len(with_evidence) / len(claims)

        issues = []
        for c in claims:
            if not c.has_evidence():
                if c.claim_type == "fact":
                    issues.append(f"CRITICAL: Fact claim {c.claim_id} has no evidence")
                else:
                    issues.append(f"WARNING: {c.claim_type} claim {c.claim_id} has no evidence")

        passed = rate >= self.min_rate
        if self.reject_assertions:
            fact_claims = [c for c in claims if c.claim_type == "fact"]
            facts_with_evidence = [c for c in fact_claims if c.has_evidence()]
            if fact_claims and len(facts_with_evidence) < len(fact_claims):
                passed = False

        return {
            "passed": passed,
            "rate": rate,
            "issues": issues,
            "claims_total": len(claims),
            "claims_with_evidence": len(with_evidence),
            "facts_without_evidence": len([c for c in claims
                                           if c.claim_type == "fact" and not c.has_evidence()])
        }


# Factory functions
def get_provenance_linker(strict: bool = True) -> ProvenanceLinker:
    """Get provenance linker instance."""
    return ProvenanceLinker(strict=strict)


def get_provenance_validator(min_rate: float = 0.95) -> ProvenanceValidator:
    """Get provenance validator instance."""
    return ProvenanceValidator(min_rate=min_rate)
