"""Ranking Explanation Generator (Phase 2-ΩΩ).

Explains why papers are ranked in their positions based on subscores
and feature importance.
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def calculate_average_subscores(papers: List[Dict]) -> Dict[str, float]:
    """Calculate average subscores across all papers.
    
    Args:
        papers: List of paper dicts with subscores
        
    Returns:
        Dict of average subscores
    """
    if not papers:
        return {}
    
    # Collect all subscore keys
    subscore_keys = set()
    for paper in papers:
        subscores = paper.get("subscores", {})
        subscore_keys.update(subscores.keys())
    
    # Calculate averages
    averages = {}
    for key in subscore_keys:
        values = [
            p.get("subscores", {}).get(key, 0.0)
            for p in papers
            if key in p.get("subscores", {})
        ]
        if values:
            averages[key] = sum(values) / len(values)
    
    return averages


def explain_ranking(
    paper: Dict,
    avg_subscores: Dict[str, float],
    top_n_strengths: int = 3,
    top_n_weaknesses: int = 2
) -> Dict[str, Any]:
    """Generate ranking explanation for a paper.
    
    Args:
        paper: Paper dict with subscores
        avg_subscores: Average subscores across all papers
        top_n_strengths: Number of top strengths to report
        top_n_weaknesses: Number of top weaknesses to report
        
    Returns:
        Dict with 'strengths', 'weaknesses', 'explanation'
    """
    subscores = paper.get("subscores", {})
    
    if not subscores or not avg_subscores:
        return {
            "strengths": [],
            "weaknesses": [],
            "explanation": "Insufficient scoring data"
        }
    
    # Calculate differences from average
    diffs = {}
    for key, value in subscores.items():
        if key in avg_subscores:
            diffs[key] = value - avg_subscores[key]
    
    # Sort by difference
    sorted_diffs = sorted(diffs.items(), key=lambda x: x[1], reverse=True)
    
    # Extract strengths and weaknesses
    strengths = [item[0] for item in sorted_diffs[:top_n_strengths] if item[1] > 0]
    weaknesses = [item[0] for item in sorted_diffs[-top_n_weaknesses:] if item[1] < 0]
    weaknesses.reverse()  # Show worst first
    
    # Generate explanation text
    strength_text = ", ".join(strengths) if strengths else "なし"
    weakness_text = ", ".join(weaknesses) if weaknesses else "なし"
    
    explanation = f"主な強み: {strength_text} | 主な弱み: {weakness_text}"
    
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "explanation": explanation
    }


def format_subscores_markdown(subscores: Dict[str, float]) -> List[str]:
    """Format subscores as markdown lines.
    
    Args:
        subscores: Dict of subscore name -> value
        
    Returns:
        List of markdown lines
    """
    lines = []
    
    # Define display order (common keys first)
    preferred_order = [
        "clinical_translation",
        "causal_strength",
        "reproducibility",
        "tme_relevance",
        "novelty",
        "evidence_quality"
    ]
    
    # Display in preferred order
    for key in preferred_order:
        if key in subscores:
            display_name = key.replace("_", " ").title()
            value = subscores[key]
            lines.append(f"- {display_name}: {value:.2f}")
    
    # Display remaining keys
    for key, value in subscores.items():
        if key not in preferred_order:
            display_name = key.replace("_", " ").title()
            lines.append(f"- {display_name}: {value:.2f}")
    
    return lines


def validate_subscores(paper: Dict) -> List[str]:
    """Validate that paper has required subscores.
    
    Args:
        paper: Paper dict
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if "subscores" not in paper:
        errors.append(f"Paper {paper.get('paper_id', 'unknown')}: Missing subscores")
        return errors
    
    subscores = paper["subscores"]
    
    if not isinstance(subscores, dict):
        errors.append(f"Paper {paper.get('paper_id', 'unknown')}: Subscores is not a dict")
        return errors
    
    if len(subscores) == 0:
        errors.append(f"Paper {paper.get('paper_id', 'unknown')}: Subscores is empty")
    
    # Check for invalid values
    for key, value in subscores.items():
        if not isinstance(value, (int, float)):
            errors.append(
                f"Paper {paper.get('paper_id', 'unknown')}: "
                f"Subscore '{key}' has invalid type {type(value)}"
            )
        elif value < 0 or value > 1:
            errors.append(
                f"Paper {paper.get('paper_id', 'unknown')}: "
                f"Subscore '{key}' out of range [0, 1]: {value}"
            )
    
    return errors
