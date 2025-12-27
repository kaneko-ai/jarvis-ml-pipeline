"""Runs Index Management (Phase 2-ΩΩ).

Maintains a searchable index of all JARVIS runs for tracking and comparison.
"""
from pathlib import Path
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


def append_run_index(
    run_dir: Path,
    run_metadata: Dict[str, Any],
    index_file: Path = None
) -> None:
    """Append run information to index.
    
    Args:
        run_dir: Path to run directory
        run_metadata: Metadata dict with goal, dataset, model etc.
        index_file: Path to index file (defaults to runs_index.jsonl)
    """
    if index_file is None:
        index_file = Path("runs_index.jsonl")
    
    # Load eval_summary for gate results
    eval_file = run_dir / "eval_summary.json"
    gate_passed = None
    
    if eval_file.exists():
        with open(eval_file, "r", encoding="utf-8") as f:
            eval_summary = json.load(f)
            gate_passed = eval_summary.get("gate_passed")
    
    # Build index entry
    entry = {
        "run_id": run_dir.name,
        "goal": run_metadata.get("goal", ""),
        "dataset": run_metadata.get("dataset", ""),
        "profile": run_metadata.get("profile", "balanced"),
        "model_name": run_metadata.get("model_name", ""),
        "model_version": run_metadata.get("model_version", ""),
        "gate_passed": gate_passed,
        "timestamp": run_metadata.get("timestamp", ""),
    }
    
    # Add key metrics if available
    cost_file = run_dir / "cost_report.json"
    if cost_file.exists():
        with open(cost_file, "r", encoding="utf-8") as f:
            cost_report = json.load(f)
            totals = cost_report.get("totals", {})
            entry["total_tokens"] = totals.get("total_tokens", 0)
            entry["total_duration_ms"] = totals.get("total_duration_ms", 0)
    
    # Append to index
    with open(index_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    logger.info(f"Run {run_dir.name} added to index")


def search_runs_index(
    query: str = None,
    gate_passed: bool = None,
    dataset: str = None,
    index_file: Path = None
) -> list:
    """Search runs index.
    
    Args:
        query: Search term for goal
        gate_passed: Filter by gate status
        dataset: Filter by dataset name
        index_file: Path to index file
        
    Returns:
        List of matching run entries
    """
    if index_file is None:
        index_file = Path("runs_index.jsonl")
    
    if not index_file.exists():
        return []
    
    matches = []
    
    with open(index_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            
            entry = json.loads(line)
            
            # Apply filters
            if query and query not in entry.get("goal", ""):
                continue
            
            if gate_passed is not None and entry.get("gate_passed") != gate_passed:
                continue
            
            if dataset and entry.get("dataset") != dataset:
                continue
            
            matches.append(entry)
    
    return matches
