"""jarvis screen - Active Learning paper screening (B-4).

Uses ActiveLearningEngine to efficiently screen papers for relevance.
Supports both interactive mode (human labels) and auto mode (keyword-based).

Input: JSON array of papers (from pipeline output) or JSONL file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def run_screen(args) -> int:
    """Run active learning screening session."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"  Error: File not found: {input_path}")
        return 1

    auto_mode = getattr(args, "auto", False)
    batch_size = getattr(args, "batch_size", 5)
    budget = getattr(args, "budget", 0.5)

    # Load papers (support both JSON array and JSONL)
    papers = _load_papers(input_path)
    if not papers:
        print("  Error: No papers found in input file.")
        return 1

    papers_with_abstract = [p for p in papers if p.get("abstract", "").strip()]
    if len(papers_with_abstract) < 3:
        print(f"  Need at least 3 papers with abstracts. Found: {len(papers_with_abstract)}")
        return 1

    print(f"  Active Learning Screening")
    print(f"  Papers: {len(papers_with_abstract)} (with abstracts)")
    print(f"  Mode: {'Auto (keyword)' if auto_mode else 'Interactive'}")
    print(f"  Batch size: {batch_size}")
    print(f"  Budget: {budget:.0%} of papers")
    print()

    # Extract features
    instances = {}
    paper_map = {}
    for i, p in enumerate(papers_with_abstract):
        pid = p.get("doi") or p.get("pmid") or p.get("title", f"paper_{i}")[:40]
        instances[pid] = _extract_features(p)
        paper_map[pid] = p

    # Initialize engine
    try:
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig
    except ImportError as e:
        print(f"  Error: Could not import ActiveLearningEngine: {e}")
        return 1

    config = ALConfig(
        batch_size=batch_size,
        initial_samples=min(3, len(instances)),
        budget_ratio=budget,
        max_iterations=50,
    )

    engine = ActiveLearningEngine(config)
    engine.initialize(instances)

    labeled = {}
    iteration = 0

    while not engine.should_stop():
        iteration += 1
        stats = engine.get_stats()
        print(f"  --- Iteration {iteration} ---")
        print(f"  Labeled: {stats.labeled_instances}/{stats.total_instances} | Relevant: {stats.relevant_found}")

        to_label = engine.get_next_query()
        if not to_label:
            print("  No more papers to label.")
            break

        batch_labels = {}
        for pid in to_label:
            paper = paper_map.get(pid, {})
            title = paper.get("title", "Unknown")[:70]
            abstract = paper.get("abstract", "")[:200]

            if auto_mode:
                label = _auto_label(paper)
                label_str = "RELEVANT" if label == 1 else "not relevant"
                print(f"    [{pid[:30]}] {title} -> {label_str}")
            else:
                print()
                print(f"    Title: {title}")
                print(f"    Abstract: {abstract}...")
                evidence = paper.get("evidence_level", "?")
                score = paper.get("quality_score", "?")
                print(f"    Evidence: {evidence} | Score: {score}")

                while True:
                    response = input("    Relevant? (y/n/q to quit): ").strip().lower()
                    if response in ("y", "yes", "1"):
                        label = 1
                        break
                    elif response in ("n", "no", "0"):
                        label = 0
                        break
                    elif response == "q":
                        print("  Quitting early...")
                        engine._state = engine._state.__class__("stopped")
                        break
                    print("    Please enter y, n, or q")

                if response == "q":
                    break

            batch_labels[pid] = label
            labeled[pid] = {
                "paper_id": pid,
                "title": paper.get("title", ""),
                "label": label,
                "label_text": "relevant" if label == 1 else "not_relevant",
            }

        engine.update_batch(batch_labels)

    # Final report
    stats = engine.get_stats()
    print()
    print("=" * 50)
    print("  Screening Complete")
    print("=" * 50)
    print(f"  Total papers: {stats.total_instances}")
    print(f"  Labeled: {stats.labeled_instances}")
    print(f"  Relevant: {stats.relevant_found}")
    print(f"  Estimated recall: {stats.estimated_recall:.1%}")
    work_saved = 1 - stats.labeled_instances / max(1, stats.total_instances)
    print(f"  Work saved: {work_saved:.1%}")
    print()

    # Get predictions for unlabeled
    predictions = engine.get_predictions()
    predicted_relevant = [pid for pid, prob in predictions.items() if prob > 0.5]
    print(f"  Predicted relevant (unlabeled): {len(predicted_relevant)}")

    # Save output
    output_path = str(input_path).replace(".json", "_screened.json")
    output_data = {
        "stats": stats.to_dict(),
        "labeled": list(labeled.values()),
        "predicted_relevant": [
            {"paper_id": pid, "probability": round(predictions.get(pid, 0), 3),
             "title": paper_map.get(pid, {}).get("title", "")}
            for pid in predicted_relevant
        ],
    }
    Path(output_path).write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Results saved to: {output_path}")

    return 0


def _load_papers(path: Path) -> list[dict]:
    """Load papers from JSON array or JSONL file."""
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    else:
        papers = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    papers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return papers


def _extract_features(paper: dict) -> list[float]:
    """Extract simple keyword-based features from a paper."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

    keywords = [
        "randomized", "controlled", "trial", "rct",
        "systematic", "review", "meta-analysis",
        "cohort", "case-control", "observational",
        "prospective", "retrospective",
        "significant", "efficacy", "safety", "outcome",
        "in vitro", "in vivo", "mouse", "mice", "cell line",
    ]

    features = [1.0 if kw in text else 0.0 for kw in keywords]

    # Normalized word count
    features.append(min(len(text.split()) / 1000, 1.0))

    # Evidence level as feature
    evidence = paper.get("evidence_level", "5")
    try:
        level = int(str(evidence)[0]) if evidence and evidence != "unknown" else 5
    except (ValueError, IndexError):
        level = 5
    features.append((5 - level) / 4.0)  # Higher for better evidence

    # Citation count (log-normalized)
    import math
    citations = paper.get("citation_count", 0) or 0
    features.append(min(math.log10(citations + 1) / 4, 1.0))

    return features


def _auto_label(paper: dict) -> int:
    """Auto-label based on keywords (for non-interactive testing)."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    relevant_keywords = [
        "randomized", "clinical trial", "rct", "meta-analysis",
        "systematic review", "controlled trial", "efficacy",
    ]
    return 1 if any(kw in text for kw in relevant_keywords) else 0
