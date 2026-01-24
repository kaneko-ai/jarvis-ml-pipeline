"""Ranking Feature Extraction (Phase 26).

Computes features for Learning to Rank (LTR) models.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)

class RankingFeatures:
    """Feature extractor for query-document pairs."""

    def __init__(self):
        pass

    def extract(self, query: str, doc: Dict[str, Any], query_vec: np.ndarray = None, doc_vec: np.ndarray = None) -> Dict[str, float]:
        """Compute ranking features."""
        features = {}
        
        doc_text = doc.get("text", "")
        doc_title = doc.get("title", "")
        
        # 1. Text Match Features
        features["title_match"] = 1.0 if query.lower() in doc_title.lower() else 0.0
        features["exact_match"] = 1.0 if query.lower() in doc_text.lower() else 0.0
        features["query_len"] = len(query.split())
        features["doc_len"] = len(doc_text.split())
        
        # 2. Retrieval Scores (if available)
        features["bm25_score"] = doc.get("bm25_score", 0.0)
        
        # 3. Vector Similarity (if vectors provided)
        if query_vec is not None and doc_vec is not None:
            features["cosine_sim"] = float(np.dot(query_vec, doc_vec))
        else:
            features["cosine_sim"] = doc.get("vector_score", 0.0)

        # 4. Metadata Features
        features["has_doi"] = 1.0 if doc.get("doi") else 0.0
        features["year"] = float(doc.get("year", 0))
        
        return features

    def extract_batch(self, query: str, docs: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """Extract features for a batch of documents."""
        # Note: In a real implementation, we'd handle vector batching here
        return [self.extract(query, doc) for doc in docs]
