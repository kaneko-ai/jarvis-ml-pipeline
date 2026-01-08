"""Ranking Evaluation (Phase 2-ΩΩ P2).

Evaluates Learning-to-Rank performance using NDCG and MAP metrics.
"""
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def calculate_ndcg(
    ranked_ids: list[str],
    golden_ranks: dict[str, int],
    k: int = 10
) -> float:
    """Calculate Normalized Discounted Cumulative Gain at K.
    
    Args:
        ranked_ids: List of paper IDs in predicted rank order
        golden_ranks: Dict mapping paper_id to ideal rank (1=best)
        k: Cutoff position
        
    Returns:
        NDCG@K score (0-1)
    """
    def dcg(ranks: list[int], k: int) -> float:
        """Discounted Cumulative Gain."""
        import math
        dcg_sum = 0.0
        for i, rank in enumerate(ranks[:k]):
            # Relevance = inverse of rank (1/rank)
            relevance = 1.0 / rank if rank > 0 else 0.0
            # Discount by position
            dcg_sum += relevance / math.log2(i + 2)  # i+2 to avoid log(1)
        return dcg_sum

    # Get predicted ranks
    predicted_ranks = []
    for paper_id in ranked_ids[:k]:
        ideal_rank = golden_ranks.get(paper_id, 999)  # 999 if not in golden set
        predicted_ranks.append(ideal_rank)

    # Get ideal ranks (sorted)
    ideal_ranks = sorted(golden_ranks.values())[:k]

    # Calculate DCG
    dcg_score = dcg(predicted_ranks, k)
    ideal_dcg = dcg(ideal_ranks, k)

    # Normalize
    if ideal_dcg == 0:
        return 0.0

    ndcg = dcg_score / ideal_dcg

    return ndcg


def calculate_map(
    ranked_ids: list[str],
    relevant_ids: set
) -> float:
    """Calculate Mean Average Precision.
    
    Args:
        ranked_ids: List of paper IDs in predicted rank order
        relevant_ids: Set of relevant paper IDs
        
    Returns:
        MAP score (0-1)
    """
    if len(relevant_ids) == 0:
        return 0.0

    relevant_count = 0
    precision_sum = 0.0

    for i, paper_id in enumerate(ranked_ids):
        if paper_id in relevant_ids:
            relevant_count += 1
            precision_at_k = relevant_count / (i + 1)
            precision_sum += precision_at_k

    if relevant_count == 0:
        return 0.0

    avg_precision = precision_sum / len(relevant_ids)

    return avg_precision


def evaluate_ranking(
    predictions_file: Path,
    golden_file: Path
) -> dict[str, Any]:
    """Evaluate ranking against golden set.
    
    Args:
        predictions_file: Path to predicted scores.json
        golden_file: Path to golden ranking dataset
        
    Returns:
        Dict with NDCG@10, MAP, etc.
    """
    # Load predictions
    with open(predictions_file, encoding="utf-8") as f:
        predictions = json.load(f)

    predicted_papers = predictions.get("papers", [])
    ranked_ids = [p["paper_id"] for p in sorted(predicted_papers, key=lambda x: x.get("overall_score", 0), reverse=True)]

    # Load golden set
    golden_ranks = {}
    relevant_ids = set()

    with open(golden_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                paper_id = entry["paper_id"]
                rank = entry["rank"]
                golden_ranks[paper_id] = rank
                relevant_ids.add(paper_id)

    # Calculate metrics
    ndcg_10 = calculate_ndcg(ranked_ids, golden_ranks, k=10)
    map_score = calculate_map(ranked_ids, relevant_ids)

    return {
        "ndcg@10": ndcg_10,
        "map": map_score,
        "golden_set_size": len(golden_ranks),
        "predicted_set_size": len(ranked_ids)
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python ranking_eval.py <predictions.json> <golden_set.jsonl>")
        sys.exit(1)

    predictions_file = Path(sys.argv[1])
    golden_file = Path(sys.argv[2])

    results = evaluate_ranking(predictions_file, golden_file)

    print(f"NDCG@10: {results['ndcg@10']:.3f}")
    print(f"MAP: {results['map']:.3f}")
    print(f"Golden set: {results['golden_set_size']} papers")
