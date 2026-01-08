"""
JARVIS Snapshot Manager

M2: 再現性完備のためのスナップショット管理
- 検索クエリ・結果・取得内容を保存
- 再実行時にスナップショットを優先利用
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class QueryPackage:
    """検索クエリパッケージ."""
    query: str
    source: str = "pubmed"
    filters: dict[str, Any] = field(default_factory=dict)
    max_results: int = 20

    @property
    def query_hash(self) -> str:
        """クエリのハッシュ値."""
        content = f"{self.query}|{self.source}|{json.dumps(self.filters, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class SearchResultItem:
    """検索結果アイテム."""
    doc_id: str
    rank: int
    score: float = 0.0
    pmid: str | None = None
    pmcid: str | None = None
    title: str = ""


@dataclass
class RetrievedContent:
    """取得コンテンツ."""
    doc_id: str
    content_hash: str
    title: str = ""
    abstract: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    retrieval_status: str = "full"  # full, abstract_only, failed, cached


@dataclass
class ChunkMapping:
    """チャンクマッピング."""
    doc_id: str
    chunk_id: str
    start: int
    end: int
    section: str = ""
    text_hash: str = ""


@dataclass
class ModelIO:
    """モデル入出力."""
    stage_id: str
    model_id: str
    model_version: str = ""
    prompt_hash: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    output_hash: str = ""


@dataclass
class Snapshot:
    """スナップショット."""
    run_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    snapshot_version: str = "1"
    query_package: QueryPackage | None = None
    search_results: list[SearchResultItem] = field(default_factory=list)
    retrieved_content: list[RetrievedContent] = field(default_factory=list)
    chunk_mapping: list[ChunkMapping] = field(default_factory=list)
    model_io: list[ModelIO] = field(default_factory=list)
    is_degraded: bool = False
    degraded_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "snapshot_version": self.snapshot_version,
            "query_package": asdict(self.query_package) if self.query_package else None,
            "search_results": {
                "total_count": len(self.search_results),
                "returned_count": len(self.search_results),
                "results": [asdict(r) for r in self.search_results]
            },
            "retrieved_content": [asdict(c) for c in self.retrieved_content],
            "chunk_mapping": [asdict(m) for m in self.chunk_mapping],
            "model_io": [asdict(io) for io in self.model_io],
            "degraded": {
                "is_degraded": self.is_degraded,
                "reasons": self.degraded_reasons
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Snapshot:
        """辞書から生成."""
        snapshot = cls(
            run_id=data["run_id"],
            created_at=data.get("created_at", ""),
            snapshot_version=data.get("snapshot_version", "1")
        )

        # QueryPackage
        if data.get("query_package"):
            qp = data["query_package"]
            snapshot.query_package = QueryPackage(
                query=qp["query"],
                source=qp.get("source", "pubmed"),
                filters=qp.get("filters", {}),
                max_results=qp.get("max_results", 20)
            )

        # Search results
        if data.get("search_results", {}).get("results"):
            for r in data["search_results"]["results"]:
                snapshot.search_results.append(SearchResultItem(**r))

        # Retrieved content
        for c in data.get("retrieved_content", []):
            snapshot.retrieved_content.append(RetrievedContent(**c))

        # Chunk mapping
        for m in data.get("chunk_mapping", []):
            snapshot.chunk_mapping.append(ChunkMapping(**m))

        # Model IO
        for io in data.get("model_io", []):
            snapshot.model_io.append(ModelIO(**io))

        # Degraded
        if data.get("degraded"):
            snapshot.is_degraded = data["degraded"].get("is_degraded", False)
            snapshot.degraded_reasons = data["degraded"].get("reasons", [])

        return snapshot


class SnapshotManager:
    """スナップショット管理."""

    def __init__(self, base_path: str = "artifacts", compress: bool = True):
        """
        初期化.
        
        Args:
            base_path: スナップショット保存先ベースパス
            compress: gzip圧縮するか
        """
        self.base_path = Path(base_path)
        self.compress = compress

    def _get_snapshot_path(self, run_id: str) -> Path:
        """スナップショットパスを取得."""
        dir_path = self.base_path / run_id / "snapshot"
        filename = "snapshot.json.gz" if self.compress else "snapshot.json"
        return dir_path / filename

    def save(self, snapshot: Snapshot) -> Path:
        """
        スナップショットを保存.
        
        Args:
            snapshot: 保存するスナップショット
        
        Returns:
            保存先パス
        """
        path = self._get_snapshot_path(snapshot.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2)

        if self.compress:
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                f.write(data)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(data)

        return path

    def load(self, run_id: str) -> Snapshot | None:
        """
        スナップショットを読み込み.
        
        Args:
            run_id: 実行ID
        
        Returns:
            スナップショット（存在しない場合None）
        """
        path = self._get_snapshot_path(run_id)

        if not path.exists():
            # 非圧縮版も試す
            alt_path = path.parent / "snapshot.json"
            if alt_path.exists():
                path = alt_path
            else:
                return None

        try:
            if path.suffix == '.gz':
                with gzip.open(path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)

            return Snapshot.from_dict(data)

        except Exception as e:
            print(f"Failed to load snapshot: {e}")
            return None

    def exists(self, run_id: str) -> bool:
        """スナップショットが存在するか."""
        path = self._get_snapshot_path(run_id)
        alt_path = path.parent / "snapshot.json"
        return path.exists() or alt_path.exists()

    def get_content_hash(self, content: str) -> str:
        """コンテンツのハッシュを計算."""
        return hashlib.sha256(content.encode()).hexdigest()


# グローバルマネージャ
_manager: SnapshotManager | None = None


def get_snapshot_manager(base_path: str = "artifacts") -> SnapshotManager:
    """スナップショットマネージャを取得."""
    global _manager
    if _manager is None:
        _manager = SnapshotManager(base_path)
    return _manager
