"""Citation Relevance Scorer.

Per V4-T03, this provides hybrid relevance scoring.
Uses BM25 + optional embedding distance.
"""
from __future__ import annotations


def bm25_score(
    query: str,
    document: str,
    k1: float = 1.5,
    b: float = 0.75,
    avg_doc_len: float = 100,
) -> float:
    """Calculate BM25 score.

    Args:
        query: Query text.
        document: Document text.
        k1: Term frequency saturation parameter.
        b: Document length normalization parameter.
        avg_doc_len: Average document length.

    Returns:
        BM25 score.
    """
    query_terms = query.lower().split()
    doc_terms = document.lower().split()
    doc_len = len(doc_terms)

    if doc_len == 0:
        return 0.0

    # Term frequencies
    tf = {}
    for term in doc_terms:
        tf[term] = tf.get(term, 0) + 1

    score = 0.0
    for term in query_terms:
        if term in tf:
            freq = tf[term]
            numerator = freq * (k1 + 1)
            denominator = freq + k1 * (1 - b + b * doc_len / avg_doc_len)
            score += numerator / denominator

    return score


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity."""
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())

    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union


def score_relevance(
    query: str,
    evidence_text: str,
    use_embedding: bool = False,
) -> dict:
    """Score relevance of evidence to query.

    Args:
        query: Query/claim text.
        evidence_text: Evidence text.
        use_embedding: Whether to use embedding (placeholder).

    Returns:
        Relevance score dict.
    """
    if not query or not evidence_text:
        return {"score": 0.0, "method": "none", "threshold_met": False}

    # BM25 score
    bm25 = bm25_score(query, evidence_text)

    # Jaccard as secondary
    jaccard = jaccard_similarity(query, evidence_text)

    # Combine (weighted)
    combined = 0.7 * min(bm25 / 5, 1.0) + 0.3 * jaccard

    # Threshold from registry
    threshold = 0.3  # Would come from ScoreRegistry

    return {
        "score": round(combined, 3),
        "bm25": round(bm25, 3),
        "jaccard": round(jaccard, 3),
        "method": "bm25+jaccard",
        "threshold": threshold,
        "threshold_met": combined >= threshold,
    }


def filter_by_relevance(
    query: str,
    evidences: list[tuple[str, str]],  # (id, text) pairs
    min_score: float = 0.3,
) -> list[tuple[str, float]]:
    """Filter evidences by relevance.

    Args:
        query: Query text.
        evidences: List of (id, text) tuples.
        min_score: Minimum relevance score.

    Returns:
        List of (id, score) tuples that pass threshold.
    """
    results = []

    for eid, text in evidences:
        rel = score_relevance(query, text)
        if rel["score"] >= min_score:
            results.append((eid, rel["score"]))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results
