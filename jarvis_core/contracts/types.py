"""
JARVIS Contracts Module - I/O契約、型、スキーマ

全モジュールが守るべき共通I/O契約を定義。
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class CachePolicy(Enum):
    """キャッシュポリシー."""
    NONE = "none"           # キャッシュなし
    AGGRESSIVE = "aggressive"  # 積極的キャッシュ
    CONSERVATIVE = "conservative"  # 保守的キャッシュ
    READ_ONLY = "read_only"   # 読み取りのみ


class DeviceType(Enum):
    """デバイスタイプ."""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon
    AUTO = "auto"


@dataclass
class RuntimeConfig:
    """
    Runtime configuration.
    
    Attributes:
        device: CPU/GPU設定
        device_map: マルチGPU時のマッピング
        batch_size: バッチサイズ
        timeout_seconds: タイムアウト（秒）
        cache_policy: キャッシュポリシー
        seed: 再現性のためのシード
        max_memory_gb: 最大メモリ使用量
    """
    device: DeviceType = DeviceType.AUTO
    device_map: Optional[Dict[str, str]] = None
    batch_size: int = 32
    timeout_seconds: int = 300
    cache_policy: CachePolicy = CachePolicy.AGGRESSIVE
    seed: Optional[int] = 42
    max_memory_gb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device.value,
            "device_map": self.device_map,
            "batch_size": self.batch_size,
            "timeout_seconds": self.timeout_seconds,
            "cache_policy": self.cache_policy.value,
            "seed": self.seed,
            "max_memory_gb": self.max_memory_gb
        }


@dataclass
class TaskContext:
    """
    タスクコンテキスト - 全モジュール共通の入力契約.
    
    Attributes:
        goal: タスクの目標
        domain: ドメイン（免疫/腫瘍/代謝等）
        constraints: 制約条件
        seed: 再現性シード
        timestamp: タイムスタンプ
        run_id: 実行ID
        user_id: ユーザーID（オプション）
        priority: 優先度（1=最高）
    """
    goal: str
    domain: str = "general"
    constraints: List[str] = field(default_factory=list)
    seed: int = 42
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    user_id: Optional[str] = None
    priority: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskContext":
        return cls(**data)


@dataclass
class EvidenceLink:
    """
    根拠リンク - Provenanceの核心.
    
    Attributes:
        doc_id: ドキュメントID（pmid:123, doi:xxx等）
        section: セクション（Title, Abstract, Methods, Results等）
        chunk_id: チャンクID
        start: 開始位置（文字）
        end: 終了位置（文字）
        confidence: 信頼度（0-1）
        text: 引用テキスト（オプション）
    """
    doc_id: str
    section: str
    chunk_id: str
    start: int
    end: int
    confidence: float
    text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def validate(self) -> bool:
        """Validate the evidence link."""
        if not self.doc_id or not self.chunk_id:
            return False
        if self.start < 0 or self.end < self.start:
            return False
        if not 0 <= self.confidence <= 1:
            return False
        return True


@dataclass
class Claim:
    """
    主張 - evidence_linksを持つ.
    
    Attributes:
        claim_id: 主張ID
        claim_text: 主張テキスト
        evidence: 根拠リンクのリスト
        claim_type: 主張タイプ（fact, hypothesis, opinion）
        confidence: 総合信頼度
    """
    claim_id: str
    claim_text: str
    evidence: List[EvidenceLink] = field(default_factory=list)
    claim_type: str = "fact"
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "evidence": [e.to_dict() for e in self.evidence],
            "claim_type": self.claim_type,
            "confidence": self.confidence
        }
    
    def has_evidence(self) -> bool:
        """Check if claim has at least one evidence link."""
        return len(self.evidence) > 0
    
    def evidence_rate(self) -> float:
        """Calculate evidence quality rate."""
        if not self.evidence:
            return 0.0
        return sum(e.confidence for e in self.evidence) / len(self.evidence)


@dataclass
class Paper:
    """論文情報."""
    doc_id: str
    title: str
    abstract: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    sections: Dict[str, str] = field(default_factory=dict)
    chunks: Dict[str, str] = field(default_factory=dict)
    embeddings: Optional[Dict[str, List[float]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Score:
    """評価スコア."""
    name: str
    value: float
    explanation: str
    evidence: List[EvidenceLink] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "explanation": self.explanation,
            "evidence": [e.to_dict() for e in self.evidence]
        }


@dataclass
class Artifacts:
    """
    成果物コンテナ - パイプライン間で受け渡す.
    
    Attributes:
        papers: 論文リスト
        chunks: チャンク（doc_id -> chunk_id -> text）
        embeddings: 埋め込み（chunk_id -> vector）
        claims: 主張リスト
        scores: スコアマップ
        graphs: グラフデータ
        summaries: 要約
        designs: 実験設計
        metadata: メタデータ
    """
    papers: List[Paper] = field(default_factory=list)
    chunks: Dict[str, Dict[str, str]] = field(default_factory=dict)
    embeddings: Dict[str, List[float]] = field(default_factory=dict)
    claims: List[Claim] = field(default_factory=list)
    scores: Dict[str, Score] = field(default_factory=dict)
    graphs: Dict[str, Any] = field(default_factory=dict)
    summaries: Dict[str, str] = field(default_factory=dict)
    designs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "papers": [p.to_dict() for p in self.papers],
            "chunks": self.chunks,
            "embeddings": self.embeddings,
            "claims": [c.to_dict() for c in self.claims],
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "graphs": self.graphs,
            "summaries": self.summaries,
            "designs": self.designs,
            "metadata": self.metadata
        }
    
    def add_paper(self, paper: Paper) -> None:
        self.papers.append(paper)
    
    def add_claim(self, claim: Claim) -> None:
        self.claims.append(claim)
    
    def get_provenance_rate(self) -> float:
        """Calculate overall provenance rate."""
        if not self.claims:
            return 0.0
        with_evidence = sum(1 for c in self.claims if c.has_evidence())
        return with_evidence / len(self.claims)


@dataclass
class Metrics:
    """実行メトリクス."""
    execution_time_ms: float = 0.0
    provenance_rate: float = 0.0
    claims_total: int = 0
    claims_with_evidence: int = 0
    papers_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResultBundle:
    """
    結果バンドル - 全出力の共通形式.
    
    Attributes:
        outputs: 出力データ
        provenance: 根拠情報（evidence_links）
        metrics: メトリクス
        logs: ログメッセージ
        diffs: 差分情報（再実行時）
        success: 成功フラグ
        error: エラーメッセージ（失敗時）
    """
    outputs: Dict[str, Any] = field(default_factory=dict)
    provenance: List[Claim] = field(default_factory=list)
    metrics: Metrics = field(default_factory=Metrics)
    logs: List[str] = field(default_factory=list)
    diffs: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "outputs": self.outputs,
            "provenance": [c.to_dict() for c in self.provenance],
            "metrics": self.metrics.to_dict(),
            "logs": self.logs,
            "diffs": self.diffs,
            "success": self.success,
            "error": self.error
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def validate_provenance(self, min_rate: float = 0.95) -> bool:
        """Validate provenance rate meets threshold."""
        if not self.provenance:
            return False
        with_evidence = sum(1 for c in self.provenance if c.has_evidence())
        rate = with_evidence / len(self.provenance)
        return rate >= min_rate
    
    def add_log(self, message: str) -> None:
        self.logs.append(f"[{datetime.utcnow().isoformat()}] {message}")
    
    def mark_error(self, error: str) -> None:
        self.success = False
        self.error = error
        self.add_log(f"ERROR: {error}")


# Type aliases
ArtifactsDelta = Dict[str, Any]  # 差分を返す時の型
