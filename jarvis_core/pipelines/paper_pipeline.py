"""
JARVIS Paper Pipeline

Step 41-60: 文献パイプライン工具化
- index必須
- paper取得→chunk→根拠→要約
- sources記録
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
class IndexMeta:
    """索引メタ情報（Step 45）."""
    index_id: str
    created_at: str
    source_path: str
    chunk_strategy: str
    chunk_count: int
    paper_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "index_id": self.index_id,
            "created_at": self.created_at,
            "source_path": self.source_path,
            "chunk_strategy": self.chunk_strategy,
            "chunk_count": self.chunk_count,
            "paper_count": self.paper_count,
        }


@dataclass
class PaperSource:
    """論文ソース記録（Step 46-47）."""
    paper_id: str
    title: str
    source: str  # pubmed, arxiv, local
    doi: str | None = None
    pmid: str | None = None
    url: str | None = None
    fulltext_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "source": self.source,
            "doi": self.doi,
            "pmid": self.pmid,
            "url": self.url,
            "fulltext_available": self.fulltext_available,
        }


class PaperPipeline:
    """文献パイプライン.
    
    Step 41-60: 工具化された文献処理
    """

    def __init__(
        self,
        indexes_dir: str = "indexes",
        require_index: bool = True,
    ):
        """初期化."""
        self.indexes_dir = Path(indexes_dir)
        self.require_index = require_index

        # 実行記録
        self.indexes_used: list[str] = []
        self.papers_used: list[PaperSource] = []
        self.fetch_errors: list[dict[str, Any]] = []

    def check_index(self, index_id: str) -> bool:
        """index存在チェック（Step 42-43）."""
        index_path = self.indexes_dir / index_id
        meta_path = index_path / "meta.json"
        return meta_path.exists()

    def load_index_meta(self, index_id: str) -> IndexMeta | None:
        """indexメタ読み込み."""
        meta_path = self.indexes_dir / index_id / "meta.json"
        if not meta_path.exists():
            return None

        with open(meta_path, encoding='utf-8') as f:
            data = json.load(f)

        return IndexMeta(**data)

    def create_index(
        self,
        index_id: str,
        source_path: str,
        papers: list[dict[str, Any]],
        chunks: list[dict[str, Any]],
        chunk_strategy: str = "adaptive",
    ) -> IndexMeta:
        """index作成（Step 44）."""
        index_path = self.indexes_dir / index_id
        index_path.mkdir(parents=True, exist_ok=True)

        # メタ情報
        meta = IndexMeta(
            index_id=index_id,
            created_at=datetime.now().isoformat(),
            source_path=source_path,
            chunk_strategy=chunk_strategy,
            chunk_count=len(chunks),
            paper_count=len(papers),
        )

        # 保存
        with open(index_path / "meta.json", 'w', encoding='utf-8') as f:
            json.dump(meta.to_dict(), f, indent=2, ensure_ascii=False)

        with open(index_path / "chunks.jsonl", 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')

        logger.info(f"Created index: {index_id} with {len(chunks)} chunks")
        return meta

    def process_papers(
        self,
        query: str,
        index_id: str | None = None,
        max_papers: int = 10,
    ) -> dict[str, Any]:
        """論文処理パイプライン.
        
        Step 50-51: chunk→根拠→要約
        直接要約経路を閉じる
        
        Returns:
            papers, claims, evidence, warnings
        """
        warnings = []

        # Step 42: index必須チェック
        if self.require_index and index_id:
            if not self.check_index(index_id):
                warnings.append({
                    "code": "INDEX_MISSING",
                    "msg": f"Index '{index_id}' not found. Creating new index.",
                })

        if index_id:
            self.indexes_used.append(index_id)

        # Step 46-47: 論文取得と記録
        papers = []
        claims = []
        evidence = []

        # TODO: 実際の取得処理（PubMed/arXiv API）
        # ここではスケルトン

        return {
            "papers": papers,
            "claims": claims,
            "evidence": evidence,
            "warnings": warnings,
            "indexes_used": self.indexes_used,
            "papers_used": [p.to_dict() for p in self.papers_used],
        }

    def record_paper_source(
        self,
        paper_id: str,
        title: str,
        source: str,
        **kwargs,
    ) -> None:
        """論文ソースを記録（Step 47）."""
        self.papers_used.append(PaperSource(
            paper_id=paper_id,
            title=title,
            source=source,
            **kwargs,
        ))

    def record_fetch_error(
        self,
        paper_id: str,
        error: str,
        retry_count: int = 0,
    ) -> None:
        """取得エラーを記録（Step 49, 54）."""
        self.fetch_errors.append({
            "paper_id": paper_id,
            "error": error,
            "retry_count": retry_count,
            "timestamp": datetime.now().isoformat(),
        })

    def get_sources_summary(self) -> dict[str, Any]:
        """ソースサマリー（Step 56）."""
        return {
            "indexes_used": self.indexes_used,
            "papers_used": len(self.papers_used),
            "papers_sources": [p.to_dict() for p in self.papers_used],
            "fetch_errors": self.fetch_errors,
        }
