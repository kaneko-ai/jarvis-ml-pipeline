"""BM25 Retrieval.

Per RP-14, provides lightweight BM25 ranking.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import List, Tuple


def tokenize(text: str) -> List[str]:
    """Simple tokenizer."""
    import re
    return re.findall(r'\w+', text.lower())


class BM25:
    """Simple BM25 implementation."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs: dict[str, int] = {}
        self.doc_lens: List[int] = []
        self.doc_tokens: List[List[str]] = []
        self.avg_doc_len = 0.0
        self.n_docs = 0

    def fit(self, documents: List[str]) -> "BM25":
        """Fit on documents."""
        self.n_docs = len(documents)
        self.doc_tokens = [tokenize(doc) for doc in documents]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lens) / self.n_docs if self.n_docs > 0 else 0

        # Document frequencies
        for tokens in self.doc_tokens:
            seen = set()
            for token in tokens:
                if token not in seen:
                    self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                    seen.add(token)

        return self

    def _idf(self, term: str) -> float:
        """Compute IDF."""
        df = self.doc_freqs.get(term, 0)
        return math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        """Score a single document."""
        query_tokens = tokenize(query)
        doc_tokens = self.doc_tokens[doc_idx]
        doc_len = self.doc_lens[doc_idx]

        tf = Counter(doc_tokens)
        score = 0.0

        for term in query_tokens:
            if term in tf:
                freq = tf[term]
                idf = self._idf(term)
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                score += idf * numerator / denominator

        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search for top-k documents.

        Returns:
            List of (doc_idx, score) tuples.
        """
        scores = [(i, self.score(query, i)) for i in range(self.n_docs)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
