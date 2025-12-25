"""
JARVIS Retrieval Plugin - SentenceTransformer Embedder

セクション別埋め込み、クエリ展開、類似度検索を提供。
CPU-only対応（torch optionalによるフォールバック）。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, Paper, RuntimeConfig, TaskContext
)


@dataclass
class EmbeddingResult:
    """埋め込み結果."""
    chunk_id: str
    vector: List[float]
    model: str
    dimension: int


@dataclass 
class SearchResult:
    """検索結果."""
    doc_id: str
    chunk_id: str
    score: float
    text: str


class QueryExpander:
    """
    クエリ展開 - MeSH/同義語を用いたクエリ拡張.
    """
    
    # 簡易同義語辞書
    SYNONYMS = {
        "cancer": ["tumor", "neoplasm", "malignancy", "carcinoma"],
        "treatment": ["therapy", "intervention", "medication"],
        "immune": ["immunological", "immunologic", "immunity"],
        "drug": ["pharmaceutical", "medication", "compound"],
        "cell": ["cellular", "cells"],
        "gene": ["genetic", "genomic", "genes"],
        "protein": ["proteomic", "proteins", "peptide"],
    }
    
    def expand(self, query: str) -> List[str]:
        """
        クエリを同義語で展開.
        
        Args:
            query: 元のクエリ
        
        Returns:
            展開されたクエリリスト（元のクエリ含む）
        """
        expanded = [query]
        query_lower = query.lower()
        
        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                for syn in synonyms:
                    expanded.append(query_lower.replace(term, syn))
        
        return list(set(expanded))
    
    def decompose(self, query: str) -> List[str]:
        """
        複合クエリを分解.
        
        Args:
            query: 複合クエリ
        
        Returns:
            分解されたサブクエリリスト
        """
        # AND/OR で分割
        parts = re.split(r'\s+(?:AND|OR)\s+', query, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]


class SectionEmbedder:
    """
    セクション別埋め込み.
    
    Title, Abstract, Methods, Results を個別に埋め込む。
    SentenceTransformerが利用可能な場合は使用、なければ簡易ベクトル。
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # Default for MiniLM
        
        # Try to load SentenceTransformer
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except ImportError:
            pass  # Fallback to simple embeddings
    
    def embed(self, text: str) -> List[float]:
        """
        テキストを埋め込む.
        
        Args:
            text: 入力テキスト
        
        Returns:
            埋め込みベクトル
        """
        if self.model:
            return self.model.encode(text).tolist()
        else:
            return self._simple_embed(text)
    
    def _simple_embed(self, text: str) -> List[float]:
        """簡易埋め込み（CPUフォールバック）."""
        # Hash-based simple embedding
        import struct
        
        words = text.lower().split()
        vector = [0.0] * self.dimension
        
        for i, word in enumerate(words[:100]):
            h = hashlib.md5(word.encode()).digest()
            for j in range(min(16, self.dimension)):
                idx = (i * 16 + j) % self.dimension
                vector[idx] += struct.unpack('b', h[j:j+1])[0] / 128.0
        
        # Normalize
        norm = sum(v*v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
    
    def embed_sections(self, paper: Paper) -> Dict[str, List[float]]:
        """
        論文のセクションを個別に埋め込む.
        
        Args:
            paper: 論文
        
        Returns:
            セクション名 -> 埋め込みベクトル
        """
        embeddings = {}
        
        # Title
        if paper.title:
            embeddings["title"] = self.embed(paper.title)
        
        # Abstract
        if paper.abstract:
            embeddings["abstract"] = self.embed(paper.abstract)
        
        # Sections
        for section_name, section_text in paper.sections.items():
            embeddings[section_name] = self.embed(section_text)
        
        return embeddings


class BM25Retriever:
    """
    BM25ベースの検索.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Tuple[str, str, str]] = []  # (doc_id, chunk_id, text)
        self.avg_doc_len = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
    
    def add_document(self, doc_id: str, chunk_id: str, text: str) -> None:
        """ドキュメントを追加."""
        self.documents.append((doc_id, chunk_id, text))
    
    def build_index(self) -> None:
        """インデックスを構築."""
        import math
        
        if not self.documents:
            return
        
        # Calculate document frequencies
        self.doc_freqs = {}
        total_len = 0
        
        for doc_id, chunk_id, text in self.documents:
            words = set(self._tokenize(text))
            total_len += len(text.split())
            for word in words:
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
        
        self.avg_doc_len = total_len / len(self.documents)
        
        # Calculate IDF
        N = len(self.documents)
        for word, df in self.doc_freqs.items():
            self.idf[word] = math.log((N - df + 0.5) / (df + 0.5) + 1)
    
    def _tokenize(self, text: str) -> List[str]:
        """トークン化."""
        return re.findall(r'\w+', text.lower())
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        検索を実行.
        
        Args:
            query: 検索クエリ
            top_k: 返す結果数
        
        Returns:
            検索結果リスト
        """
        query_terms = self._tokenize(query)
        scores = []
        
        for doc_id, chunk_id, text in self.documents:
            score = self._score_document(query_terms, text)
            scores.append((doc_id, chunk_id, text, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[3], reverse=True)
        
        results = []
        for doc_id, chunk_id, text, score in scores[:top_k]:
            results.append(SearchResult(
                doc_id=doc_id,
                chunk_id=chunk_id,
                score=score,
                text=text[:500]
            ))
        
        return results
    
    def _score_document(self, query_terms: List[str], doc_text: str) -> float:
        """BM25スコアを計算."""
        doc_words = self._tokenize(doc_text)
        doc_len = len(doc_words)
        word_counts = {}
        for w in doc_words:
            word_counts[w] = word_counts.get(w, 0) + 1
        
        score = 0.0
        for term in query_terms:
            if term not in self.idf:
                continue
            
            tf = word_counts.get(term, 0)
            idf = self.idf[term]
            
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
            
            score += idf * numerator / denominator
        
        return score


class DuplicateDetector:
    """
    重複検出 - preprint/出版版の重複を検出.
    """
    
    def __init__(self, threshold: float = 0.9):
        self.threshold = threshold
    
    def find_duplicates(self, papers: List[Paper]) -> List[Tuple[str, str]]:
        """
        重複ペアを検出.
        
        Returns:
            (doc_id1, doc_id2) のリスト
        """
        duplicates = []
        
        for i, p1 in enumerate(papers):
            for p2 in papers[i+1:]:
                similarity = self._title_similarity(p1.title, p2.title)
                if similarity >= self.threshold:
                    duplicates.append((p1.doc_id, p2.doc_id))
        
        return duplicates
    
    def _title_similarity(self, t1: str, t2: str) -> float:
        """タイトル類似度."""
        words1 = set(t1.lower().split())
        words2 = set(t2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """重複を除去（出版版を優先）."""
        duplicates = self.find_duplicates(papers)
        to_remove = set()
        
        for d1, d2 in duplicates:
            # Prefer published version (has DOI)
            p1 = next((p for p in papers if p.doc_id == d1), None)
            p2 = next((p for p in papers if p.doc_id == d2), None)
            
            if p1 and p2:
                if p1.doi and not p2.doi:
                    to_remove.add(d2)
                elif p2.doi and not p1.doi:
                    to_remove.add(d1)
                else:
                    to_remove.add(d2)  # Keep first
        
        return [p for p in papers if p.doc_id not in to_remove]


class RetrievalPlugin:
    """
    Retrieval統合プラグイン.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.expander = QueryExpander()
        self.embedder = SectionEmbedder(model_name)
        self.bm25 = BM25Retriever()
        self.dedup = DuplicateDetector()
        self.is_active = False
    
    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        """プラグインをアクティベート."""
        self.is_active = True
    
    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """
        Retrieval処理を実行.
        """
        delta: ArtifactsDelta = {}
        
        # 1. Query expansion
        expanded_queries = self.expander.expand(context.goal)
        delta["expanded_queries"] = expanded_queries
        
        # 2. Build BM25 index from papers
        for paper in artifacts.papers:
            if paper.abstract:
                self.bm25.add_document(paper.doc_id, f"{paper.doc_id}_abstract", paper.abstract)
            for section_name, section_text in paper.sections.items():
                chunk_id = f"{paper.doc_id}_{section_name}"
                self.bm25.add_document(paper.doc_id, chunk_id, section_text)
        
        self.bm25.build_index()
        
        # 3. Search
        all_results = []
        for query in expanded_queries[:3]:  # Limit expansion
            results = self.bm25.search(query, top_k=20)
            all_results.extend(results)
        
        # 4. Embed sections
        embeddings = {}
        for paper in artifacts.papers:
            paper_embeddings = self.embedder.embed_sections(paper)
            for section, vector in paper_embeddings.items():
                chunk_id = f"{paper.doc_id}_{section}"
                embeddings[chunk_id] = vector
        
        delta["embeddings"] = embeddings
        delta["search_results"] = [
            {"doc_id": r.doc_id, "chunk_id": r.chunk_id, "score": r.score}
            for r in all_results[:50]
        ]
        
        # 5. Deduplicate
        deduped = self.dedup.deduplicate(artifacts.papers)
        delta["deduplicated_count"] = len(artifacts.papers) - len(deduped)
        
        return delta
    
    def deactivate(self) -> None:
        """プラグインを非アクティベート."""
        self.is_active = False


# Factory
def get_retrieval_plugin(model_name: str = "all-MiniLM-L6-v2") -> RetrievalPlugin:
    return RetrievalPlugin(model_name)
