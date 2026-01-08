"""
JARVIS Knowledge Store

Phase8: claim/evidence蓄積検索、再利用
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StoredClaim:
    """蓄積されたclaim."""
    claim_id: str
    paper_id: str
    claim_text: str
    claim_type: str
    confidence: str
    run_id: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "paper_id": self.paper_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "confidence": self.confidence,
            "run_id": self.run_id,
            "created_at": self.created_at,
        }


@dataclass
class StoredEvidence:
    """蓄積されたevidence."""
    claim_id: str
    paper_id: str
    evidence_text: str
    source: str
    locator: dict[str, Any]
    run_id: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "paper_id": self.paper_id,
            "evidence_text": self.evidence_text,
            "source": self.source,
            "locator": self.locator,
            "run_id": self.run_id,
            "created_at": self.created_at,
        }


class KnowledgeStore:
    """知識蓄積ストア.
    
    Phase8: 過去のclaim/evidenceを蓄積し、再利用可能にする
    """

    def __init__(self, store_path: str = "knowledge_store"):
        """初期化."""
        self.store_path = Path(store_path)
        self.claims_path = self.store_path / "claims.jsonl"
        self.evidence_path = self.store_path / "evidence.jsonl"
        self.store_path.mkdir(parents=True, exist_ok=True)

    def add_claims(self, claims: list[dict[str, Any]], run_id: str) -> int:
        """claimを追加."""
        count = 0
        now = datetime.now().isoformat()

        with open(self.claims_path, 'a', encoding='utf-8') as f:
            for claim in claims:
                stored = StoredClaim(
                    claim_id=claim.get("claim_id", ""),
                    paper_id=claim.get("paper_id", ""),
                    claim_text=claim.get("claim_text", ""),
                    claim_type=claim.get("claim_type", "unknown"),
                    confidence=claim.get("confidence", "low"),
                    run_id=run_id,
                    created_at=now,
                )
                f.write(json.dumps(stored.to_dict(), ensure_ascii=False) + '\n')
                count += 1

        logger.info(f"Added {count} claims to knowledge store")
        return count

    def add_evidence(self, evidence: list[dict[str, Any]], run_id: str) -> int:
        """evidenceを追加."""
        count = 0
        now = datetime.now().isoformat()

        with open(self.evidence_path, 'a', encoding='utf-8') as f:
            for ev in evidence:
                stored = StoredEvidence(
                    claim_id=ev.get("claim_id", ""),
                    paper_id=ev.get("paper_id", ""),
                    evidence_text=ev.get("evidence_text", ""),
                    source=ev.get("source", "unknown"),
                    locator=ev.get("locator", {}),
                    run_id=run_id,
                    created_at=now,
                )
                f.write(json.dumps(stored.to_dict(), ensure_ascii=False) + '\n')
                count += 1

        logger.info(f"Added {count} evidence to knowledge store")
        return count

    def search_claims(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """claimを検索（単純キーワード）."""
        if not self.claims_path.exists():
            return []

        results = []
        query_lower = query.lower()

        with open(self.claims_path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    claim = json.loads(line)
                    if query_lower in claim.get("claim_text", "").lower():
                        results.append(claim)
                        if len(results) >= limit:
                            break

        return results

    def get_evidence_for_claim(self, claim_id: str) -> list[dict[str, Any]]:
        """claimのevidenceを取得."""
        if not self.evidence_path.exists():
            return []

        results = []
        with open(self.evidence_path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    ev = json.loads(line)
                    if ev.get("claim_id") == claim_id:
                        results.append(ev)

        return results

    def get_stats(self) -> dict[str, int]:
        """統計を取得."""
        claims_count = 0
        evidence_count = 0

        if self.claims_path.exists():
            with open(self.claims_path, encoding='utf-8') as f:
                claims_count = sum(1 for line in f if line.strip())

        if self.evidence_path.exists():
            with open(self.evidence_path, encoding='utf-8') as f:
                evidence_count = sum(1 for line in f if line.strip())

        return {
            "total_claims": claims_count,
            "total_evidence": evidence_count,
        }
