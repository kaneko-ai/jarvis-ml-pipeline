"""jarvis citation-stance - Classify citation stance between paper pairs (B-1).

For each pair of papers in the input JSON, determines whether Paper B
supports, contradicts, or is neutral to Paper A.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


def run_citation_stance(args) -> int:
    """Classify citation stance for all paper pairs in a JSON file."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"  Error: File not found: {input_path}")
        return 1

    with open(input_path, encoding="utf-8") as f:
        papers = json.load(f)

    if len(papers) < 2:
        print("  Error: Need at least 2 papers for stance classification.")
        return 1

    use_llm = getattr(args, "use_llm", True)
    print(f"  Citation Stance Classification: {len(papers)} papers")
    print(f"  Method: {'LLM (Gemini)' if use_llm else 'Keyword heuristic'}")
    print(f"  Pairs to analyze: {len(papers) * (len(papers) - 1) // 2}")
    print()

    try:
        from jarvis_core.citation.stance_classifier import StanceClassifier
    except ImportError as e:
        print(f"  Error: Could not import StanceClassifier: {e}")
        return 1

    classifier = StanceClassifier(use_llm=use_llm)
    results = []

    pair_num = 0
    total_pairs = len(papers) * (len(papers) - 1) // 2

    for i in range(len(papers)):
        for j in range(i + 1, len(papers)):
            pair_num += 1
            title_a = papers[i].get("title", "?")[:50]
            title_b = papers[j].get("title", "?")[:50]
            print(f"  [{pair_num}/{total_pairs}] {title_a}...")

            result = classifier.classify(papers[i], papers[j])

            results.append({
                "paper_a": papers[i].get("title", ""),
                "paper_b": papers[j].get("title", ""),
                "stance": result.stance.value,
                "confidence": round(result.confidence, 3),
                "reason": result.reason,
            })

            if use_llm:
                time.sleep(4)  # Gemini rate limit

    # Display summary
    print()
    stance_counts = {}
    for r in results:
        s = r["stance"]
        stance_counts[s] = stance_counts.get(s, 0) + 1

    print(f"  Stance distribution: {stance_counts}")
    print()

    # Show non-neutral results
    interesting = [r for r in results if r["stance"] != "neutral"]
    if interesting:
        print("  Notable relationships:")
        for r in interesting:
            icon = "+" if r["stance"] == "support" else "-"
            print(f"    [{icon}] {r['stance'].upper()} ({r['confidence']:.0%})")
            print(f"        A: {r['paper_a'][:60]}")
            print(f"        B: {r['paper_b'][:60]}")
            print(f"        Reason: {r['reason']}")
            print()
    else:
        print("  No support/contradiction relationships found.")

    # Save output
    output_path = str(input_path).replace(".json", "_stance.json")
    Path(output_path).write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Results saved to: {output_path}")

    return 0
