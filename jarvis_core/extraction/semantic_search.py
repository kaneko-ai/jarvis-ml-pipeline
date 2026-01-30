"""
JARVIS Semantic Search

2. セマンティック検索: Embedding + FAISS類似検索
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """検索結果."""

    doc_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class EmbeddingModel:
    """Embeddingモデル.

    SentenceTransformersまたはOpenAI Embeddingsを使用
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """初期化."""
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """モデルを遅延ロード."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                logger.warning("sentence-transformers not installed")
                self._model = None
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """テキストをembedding.

        Args:
            texts: テキストリスト

        Returns:
            Embedding行列 (n_texts, dim)
        """
        model = self._load_model()

        if model is None:
            # Fallback: ランダムembedding（デモ用）
            logger.warning("Using random embeddings (demo mode)")
            return np.random.randn(len(texts), 384).astype(np.float32)

        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """クエリをembedding."""
        return self.embed([query])[0]


class SemanticIndex:
    """セマンティックインデックス.

    FAISSを使用した類似検索
    """

    def __init__(self, embedding_model: EmbeddingModel | None = None):
        """初期化."""
        self.embedding_model = embedding_model or EmbeddingModel()
        self.documents: list[dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None
        self._index = None

    def _get_faiss(self):
        """FAISSを遅延ロード."""
        try:
            import faiss

            return faiss
        except ImportError:
            logger.warning("faiss not installed. Install with: pip install faiss-cpu")
            return None

    def add_documents(self, documents: list[dict[str, Any]], text_key: str = "text"):
        """ドキュメントを追加.

        Args:
            documents: ドキュメントリスト（text_keyを含む）
            text_key: テキストフィールド名
        """
        texts = [doc[text_key] for doc in documents]
        embeddings = self.embedding_model.embed(texts)

        if self.embeddings is None:
            self.embeddings = embeddings
            self.documents = documents
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])
            self.documents.extend(documents)

        # FAISSインデックスを再構築
        self._build_index()

        logger.info(f"Added {len(documents)} documents. Total: {len(self.documents)}")

    def _build_index(self):
        """FAISSインデックスを構築."""
        faiss = self._get_faiss()

        if faiss is None or self.embeddings is None:
            return

        dim = self.embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # Inner Product (cosine similarity)

        # 正規化
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normalized = self.embeddings / (norms + 1e-10)

        self._index.add(normalized)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """類似検索.

        Args:
            query: 検索クエリ
            top_k: 上位k件

        Returns:
            検索結果リスト
        """
        if self.embeddings is None or len(self.documents) == 0:
            return []

        query_embedding = self.embedding_model.embed_query(query)

        faiss = self._get_faiss()

        if faiss is not None and self._index is not None:
            # FAISS検索
            query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
            scores, indices = self._index.search(
                query_norm.reshape(1, -1), min(top_k, len(self.documents))
            )

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0:
                    doc = self.documents[idx]
                    results.append(
                        SearchResult(
                            doc_id=doc.get("id", str(idx)),
                            text=doc.get("text", ""),
                            score=float(score),
                            metadata=doc,
                        )
                    )
            return results

        else:
            # Fallback: numpy cosine similarity
            norms = np.linalg.norm(self.embeddings, axis=1)
            query_norm = np.linalg.norm(query_embedding)

            similarities = np.dot(self.embeddings, query_embedding) / (norms * query_norm + 1e-10)
            indices = np.argsort(similarities)[::-1][:top_k]

            results = []
            for idx in indices:
                doc = self.documents[idx]
                results.append(
                    SearchResult(
                        doc_id=doc.get("id", str(idx)),
                        text=doc.get("text", ""),
                        score=float(similarities[idx]),
                        metadata=doc,
                    )
                )
            return results

    def save(self, path: str):
        """インデックスを保存."""
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings.tolist() if self.embeddings is not None else None,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info(f"Saved index to {path}")

    def load(self, path: str):
        """インデックスを読み込み."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.documents = data["documents"]
        if data["embeddings"]:
            self.embeddings = np.array(data["embeddings"], dtype=np.float32)
            self._build_index()

        logger.info(f"Loaded index from {path}: {len(self.documents)} documents")