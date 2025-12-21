"""Retriever for finding relevant chunks based on query.

This module provides:
- BM25Retriever: Simple BM25-based retrieval for chunk selection
- search(): Find top-K relevant chunks for a query

Per RP9, this enables automatic selection of relevant evidence
for Agent citation, improving success rates.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .evidence import EvidenceStore, Chunk
from .sources import ChunkResult


@dataclass
class TokenizedDoc:
    """A tokenized document for indexing."""

    chunk_id: str
    tokens: List[str]
    term_freq: Dict[str, int] = field(default_factory=dict)


def tokenize(text: str) -> List[str]:
    """Simple tokenizer for both English and Japanese text.

    Args:
        text: Text to tokenize.

    Returns:
        List of lowercase tokens.
    """
    if not text:
        return []

    # Lowercase
    text = text.lower()

    # Split on non-alphanumeric (keeps Japanese characters)
    # This regex splits on spaces, punctuation while keeping word characters
    tokens = re.findall(r"[\w]+", text, re.UNICODE)

    # Filter very short tokens
    tokens = [t for t in tokens if len(t) > 1]

    return tokens


class BM25Retriever:
    """BM25-based retriever for chunk selection.

    BM25 is a ranking function used for information retrieval.
    This implementation is simplified for MVP but effective.

    Attributes:
        k1: Term frequency saturation parameter (default 1.5)
        b: Document length normalization (default 0.75)
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b

        self._docs: List[TokenizedDoc] = []
        self._doc_count: int = 0
        self._avg_doc_len: float = 0.0
        self._doc_freq: Dict[str, int] = {}  # term -> number of docs containing it
        self._chunk_results: Dict[str, ChunkResult] = {}  # chunk_id -> ChunkResult

    def build(
        self,
        chunks: List[ChunkResult],
        store: EvidenceStore,
    ) -> "BM25Retriever":
        """Build the index from chunks.

        Args:
            chunks: List of ChunkResult from ingestion.
            store: EvidenceStore containing the actual chunk content.

        Returns:
            Self for chaining.
        """
        self._docs = []
        self._doc_freq = {}
        self._chunk_results = {}

        total_tokens = 0

        for chunk_result in chunks:
            chunk = store.get_chunk(chunk_result.chunk_id)
            if not chunk:
                continue

            tokens = tokenize(chunk.text)
            term_freq = Counter(tokens)

            doc = TokenizedDoc(
                chunk_id=chunk_result.chunk_id,
                tokens=tokens,
                term_freq=dict(term_freq),
            )
            self._docs.append(doc)
            self._chunk_results[chunk_result.chunk_id] = chunk_result

            # Update document frequency
            for term in set(tokens):
                self._doc_freq[term] = self._doc_freq.get(term, 0) + 1

            total_tokens += len(tokens)

        self._doc_count = len(self._docs)
        self._avg_doc_len = total_tokens / max(1, self._doc_count)

        return self

    def search(
        self,
        query: str,
        k: int = 8,
    ) -> List[ChunkResult]:
        """Search for relevant chunks.

        Args:
            query: The search query.
            k: Number of top results to return.

        Returns:
            List of ChunkResult, ordered by relevance (most relevant first).
        """
        if not self._docs:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: List[tuple[str, float]] = []

        for doc in self._docs:
            score = self._score_document(query_tokens, doc)
            if score > 0:
                scores.append((doc.chunk_id, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top K
        results: List[ChunkResult] = []
        for chunk_id, _ in scores[:k]:
            if chunk_id in self._chunk_results:
                results.append(self._chunk_results[chunk_id])

        return results

    def _score_document(
        self,
        query_tokens: List[str],
        doc: TokenizedDoc,
    ) -> float:
        """Calculate BM25 score for a document.

        Args:
            query_tokens: Tokenized query.
            doc: The document to score.

        Returns:
            BM25 score.
        """
        score = 0.0
        doc_len = len(doc.tokens)

        for term in query_tokens:
            if term not in doc.term_freq:
                continue

            # Term frequency in document
            tf = doc.term_freq[term]

            # Document frequency (number of docs containing term)
            df = self._doc_freq.get(term, 0)

            # IDF component
            idf = math.log(
                (self._doc_count - df + 0.5) / (df + 0.5) + 1
            )

            # TF component with saturation
            tf_component = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_len)
            )

            score += idf * tf_component

        return score

    def __len__(self) -> int:
        return len(self._docs)


def create_retriever(
    chunks: List[ChunkResult],
    store: EvidenceStore,
    min_chunks_for_retrieval: int = 20,
) -> Optional[BM25Retriever]:
    """Create a retriever if there are enough chunks.

    Args:
        chunks: List of available chunks.
        store: EvidenceStore with chunk content.
        min_chunks_for_retrieval: Minimum chunks to justify retrieval.

    Returns:
        BM25Retriever if enough chunks, None otherwise.
    """
    if len(chunks) < min_chunks_for_retrieval:
        return None

    return BM25Retriever().build(chunks, store)


def get_relevant_chunks(
    query: str,
    chunks: List[ChunkResult],
    store: EvidenceStore,
    k: int = 8,
    min_chunks_for_retrieval: int = 20,
) -> List[ChunkResult]:
    """Get relevant chunks for a query (convenience function).

    If there are few chunks, returns all of them.
    Otherwise, uses BM25 retrieval to select top-K.

    Args:
        query: The search query.
        chunks: Available chunks.
        store: EvidenceStore with chunk content.
        k: Maximum results to return.
        min_chunks_for_retrieval: Threshold for using retrieval.

    Returns:
        List of relevant ChunkResult.
    """
    if len(chunks) <= k:
        return chunks

    if len(chunks) < min_chunks_for_retrieval:
        return chunks[:k]

    retriever = BM25Retriever().build(chunks, store)
    return retriever.search(query, k=k)
