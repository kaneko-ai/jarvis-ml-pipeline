"""
JARVIS Goldset Index

Phase2: Goldsetを検索可能にする
- embedding_text生成（Context + Reason + Outcome）
- VectorStore (goldset_index) 保存
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GoldsetEntry:
    """Goldsetエントリ."""
    context: str
    decision: str
    scores: dict[str, int]
    reason: str
    outcome: str
    embedding_text: str = ""
    embedding: list[float] = field(default_factory=list)

    def generate_embedding_text(self) -> str:
        """embedding用テキストを生成.
        
        Context + Reason + Outcome を連結。
        点数はembeddingに入れない（判断の文脈と理由を厚くする）。
        """
        parts = [
            f"Context: {self.context}",
            f"Decision: {self.decision}",
            f"Reason: {self.reason}",
            f"Outcome: {self.outcome}",
        ]
        self.embedding_text = "\n".join(parts)
        return self.embedding_text

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "context": self.context,
            "decision": self.decision,
            "scores": self.scores,
            "reason": self.reason,
            "outcome": self.outcome,
            "embedding_text": self.embedding_text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoldsetEntry:
        """辞書から生成."""
        entry = cls(
            context=data["context"],
            decision=data["decision"],
            scores=data.get("scores", {}),
            reason=data["reason"],
            outcome=data.get("outcome", ""),
        )
        entry.embedding_text = data.get("embedding_text", "")
        if not entry.embedding_text:
            entry.generate_embedding_text()
        return entry


class GoldsetIndex:
    """Goldset Index（検索可能なVectorStore）.
    
    Phase2: 類似判断検索の基盤。
    """

    def __init__(
        self,
        goldset_path: str = "configs/goldset.jsonl",
        index_path: str = "data/goldset_index"
    ):
        """
        初期化.
        
        Args:
            goldset_path: Goldsetファイルパス
            index_path: インデックス保存先
        """
        self.goldset_path = Path(goldset_path)
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)

        self._entries: list[GoldsetEntry] = []
        self._embeddings: list[list[float]] = []
        self._embed_provider = None

        self._load_goldset()

    def _load_goldset(self) -> None:
        """Goldsetを読み込み."""
        if not self.goldset_path.exists():
            logger.warning(f"Goldset not found: {self.goldset_path}")
            return

        with open(self.goldset_path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    entry = GoldsetEntry.from_dict(data)
                    self._entries.append(entry)

        logger.info(f"Loaded {len(self._entries)} goldset entries")

    def build_index(self, embed_provider=None) -> None:
        """インデックスを構築.
        
        Args:
            embed_provider: EmbedProvider（省略時はローカル）
        """
        if embed_provider:
            self._embed_provider = embed_provider
        else:
            # ローカルembeddingを使用
            from jarvis_core.providers.base import ProviderConfig, ProviderType
            from jarvis_core.providers.local_embed import LocalEmbedProvider
            config = ProviderConfig(provider_type=ProviderType.LOCAL)
            self._embed_provider = LocalEmbedProvider(config)
            self._embed_provider.initialize()

        # embedding生成
        texts = []
        for entry in self._entries:
            if not entry.embedding_text:
                entry.generate_embedding_text()
            texts.append(entry.embedding_text)

        if self._embed_provider.is_available():
            self._embeddings = self._embed_provider.embed_batch(texts)
            for i, entry in enumerate(self._entries):
                entry.embedding = self._embeddings[i]

        # インデックス保存
        self._save_index()
        logger.info(f"Built index for {len(self._entries)} entries")

    def _save_index(self) -> None:
        """インデックスを保存."""
        index_file = self.index_path / "goldset_index.json"
        data = {
            "entries": [e.to_dict() for e in self._entries],
            "embeddings": self._embeddings,
        }
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def search(self, query: str, top_k: int = 3) -> list[tuple[GoldsetEntry, float]]:
        """類似判断を検索.
        
        Args:
            query: 検索クエリ
            top_k: 上位何件
        
        Returns:
            (GoldsetEntry, similarity_score) のリスト
        """
        if not self._entries:
            return []

        # クエリをembedding
        if self._embed_provider and self._embed_provider.is_available():
            query_emb = self._embed_provider.embed(query)

            # コサイン類似度計算
            results = []
            for i, entry in enumerate(self._entries):
                if entry.embedding:
                    sim = self._cosine_similarity(query_emb, entry.embedding)
                    results.append((entry, sim))

            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        else:
            # フォールバック: キーワードマッチ
            return self._keyword_search(query, top_k)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """コサイン類似度を計算."""
        if not a or not b or len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _keyword_search(self, query: str, top_k: int) -> list[tuple[GoldsetEntry, float]]:
        """キーワードベース検索（フォールバック）."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for entry in self._entries:
            text = f"{entry.context} {entry.reason} {entry.outcome}".lower()
            text_words = set(text.split())

            intersection = query_words & text_words
            if intersection:
                score = len(intersection) / len(query_words | text_words)
                results.append((entry, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def list_all(self) -> list[GoldsetEntry]:
        """全エントリを取得."""
        return self._entries.copy()
