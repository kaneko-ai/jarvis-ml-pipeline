"""Active Learning CLI Interface.

Per JARVIS_COMPLETION_PLAN_v3 Sprint 19: AL CLI統合
Provides command-line interface for paper screening.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .engine import ActiveLearningEngine, ALConfig, ALStats


def load_papers_from_jsonl(path: Path) -> Dict[str, Dict]:
    """Load papers from JSONL file.
    
    Args:
        path: Path to JSONL file
        
    Returns:
        Dict mapping paper_id to paper data
    """
    papers = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                paper = json.loads(line)
                paper_id = paper.get("id") or paper.get("paper_id") or paper.get("pmid")
                if paper_id:
                    papers[str(paper_id)] = paper
    return papers


def extract_features(paper: Dict) -> List[float]:
    """Extract simple TF-IDF-like features from paper.
    
    Args:
        paper: Paper dictionary with title/abstract
        
    Returns:
        Feature vector (simple word count based)
    """
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    
    # Simple keyword features for screening
    keywords = [
        "randomized", "controlled", "trial", "rct",
        "systematic", "review", "meta-analysis",
        "cohort", "case-control", "observational",
        "prospective", "retrospective",
        "significant", "p<0.05", "confidence interval",
        "efficacy", "safety", "outcome",
    ]
    
    features = []
    for keyword in keywords:
        features.append(1.0 if keyword in text else 0.0)
    
    # Add word count features
    word_count = len(text.split())
    features.append(min(word_count / 1000, 1.0))  # Normalized
    
    return features


def run_screening_session(
    input_path: Path,
    output_path: Path,
    config: ALConfig,
    interactive: bool = True,
) -> ALStats:
    """Run an active learning screening session.
    
    Args:
        input_path: Path to input JSONL with papers
        output_path: Path to output JSONL with labels
        config: Active learning configuration
        interactive: Whether to prompt for labels
        
    Returns:
        Final statistics
    """
    print(f"Loading papers from {input_path}...")
    papers = load_papers_from_jsonl(input_path)
    
    if not papers:
        print("Error: No papers found in input file", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(papers)} papers")
    
    # Extract features
    print("Extracting features...")
    instances = {}
    for paper_id, paper in papers.items():
        instances[paper_id] = extract_features(paper)
    
    # Initialize engine
    engine = ActiveLearningEngine(config)
    engine.initialize(instances)
    
    print(f"\n=== Active Learning Screening ===")
    print(f"Target recall: {config.target_recall:.0%}")
    print(f"Budget ratio: {config.budget_ratio:.0%}")
    print(f"Batch size: {config.batch_size}")
    print()
    
    labeled_results = {}
    iteration = 0
    
    while not engine.should_stop():
        iteration += 1
        stats = engine.get_stats()
        
        print(f"\n--- Iteration {iteration} ---")
        print(f"Labeled: {stats.labeled_instances}/{stats.total_instances}")
        print(f"Relevant found: {stats.relevant_found}")
        print(f"Estimated recall: {stats.estimated_recall:.1%}")
        
        # Get next batch
        to_label = engine.get_next_query()
        
        if not to_label:
            print("No more instances to label")
            break
        
        for paper_id in to_label:
            paper = papers.get(paper_id, {})
            
            print(f"\n[{paper_id}]")
            print(f"Title: {paper.get('title', 'N/A')[:100]}")
            
            if interactive:
                abstract = paper.get("abstract", "N/A")[:300]
                print(f"Abstract: {abstract}...")
                
                while True:
                    response = input("\nRelevant? (y/n/q): ").strip().lower()
                    if response == "q":
                        print("Quitting early...")
                        break
                    if response in ("y", "yes", "1"):
                        label = 1
                        break
                    if response in ("n", "no", "0"):
                        label = 0
                        break
                    print("Please enter y, n, or q")
                
                if response == "q":
                    break
            else:
                # Auto-label based on keywords (for testing)
                text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
                label = 1 if any(kw in text for kw in ["randomized", "clinical trial", "rct"]) else 0
            
            engine.update(paper_id, label)
            labeled_results[paper_id] = {
                "paper_id": paper_id,
                "label": label,
                "title": paper.get("title", ""),
            }
        
        if not interactive or response == "q":
            break
    
    # Save results
    print(f"\nSaving results to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for result in labeled_results.values():
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    # Final stats
    final_stats = engine.get_stats()
    print(f"\n=== Final Statistics ===")
    print(f"Total labeled: {final_stats.labeled_instances}")
    print(f"Relevant found: {final_stats.relevant_found}")
    print(f"Estimated recall: {final_stats.estimated_recall:.1%}")
    print(f"Work saved: {1 - final_stats.labeled_instances / final_stats.total_instances:.1%}")
    
    return final_stats


def cmd_screen(args) -> None:
    """Execute screening command.
    
    Args:
        args: Parsed command line arguments
    """
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    config = ALConfig(
        batch_size=args.batch_size,
        target_recall=args.target_recall,
        budget_ratio=args.budget_ratio,
        initial_samples=args.initial_samples,
    )
    
    stats = run_screening_session(
        input_path=input_path,
        output_path=output_path,
        config=config,
        interactive=not args.auto,
    )
    
    if args.json:
        print(json.dumps(stats.to_dict(), ensure_ascii=False, indent=2))
