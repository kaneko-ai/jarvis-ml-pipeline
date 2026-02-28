"""jarvis contradict - Contradiction detection between papers (v2 T3-2).

Compares all pairs of paper abstracts and detects potential contradictions
using heuristic methods (antonym pairs + Jaccard similarity).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def run_contradict(args):
    """contradict command main logic."""
    from jarvis_core.contradiction.detector import ContradictionDetector
    from jarvis_core.contradiction.schema import Claim

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        papers = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(papers, list):
        print("Error: JSON root must be an array of papers.", file=sys.stderr)
        return 1

    # Filter papers that have abstracts
    papers_with_abstract = [
        p for p in papers
        if p.get("abstract", "").strip()
    ]

    n = len(papers_with_abstract)
    if n < 2:
        print(f"Need at least 2 papers with abstracts. Found: {n}")
        return 1

    total_pairs = n * (n - 1) // 2
    print(f"Contradiction detection:")
    print(f"  Papers with abstracts: {n}")
    print(f"  Total pairs to compare: {total_pairs}")
    print()

    # Compare all pairs
    detector = ContradictionDetector()
    contradictions = []
    pair_count = 0

    for i in range(n):
        for j in range(i + 1, n):
            paper_a = papers_with_abstract[i]
            paper_b = papers_with_abstract[j]

            claim_a = Claim(
                claim_id=str(i),
                text=paper_a.get("abstract", ""),
                paper_id=paper_a.get("title", f"Paper_{i}"),
            )
            claim_b = Claim(
                claim_id=str(j),
                text=paper_b.get("abstract", ""),
                paper_id=paper_b.get("title", f"Paper_{j}"),
            )

            try:
                result = detector.detect(claim_a, claim_b)
            except Exception:
                continue

            if result.is_contradictory:
                contradictions.append({
                    "paper_a": paper_a.get("title", ""),
                    "paper_b": paper_b.get("title", ""),
                    "score": round(result.contradiction_score, 3),
                    "type": getattr(result, "contradiction_type", ""),
                    "details": getattr(result, "details", ""),
                })

            pair_count += 1
            if pair_count % 500 == 0:
                print(f"  Progress: {pair_count}/{total_pairs} pairs...")

    # Report
    print()
    print("=" * 60)
    print("  Contradiction Report")
    print("=" * 60)
    print(f"  Pairs checked: {total_pairs}")
    print(f"  Contradictions found: {len(contradictions)}")
    print()

    if contradictions:
        contradictions.sort(key=lambda x: x["score"], reverse=True)

        for idx, c in enumerate(contradictions[:20], 1):
            title_a = c["paper_a"][:70]
            title_b = c["paper_b"][:70]
            print(f"  --- #{idx} (score: {c['score']}) ---")
            print(f"    A: {title_a}")
            print(f"    B: {title_b}")
            if c.get("type"):
                print(f"    Type: {c['type']}")
            print()

        if len(contradictions) > 20:
            print(f"  ... and {len(contradictions) - 20} more")
            print()

        # Save to JSON
        output_path = input_path.parent / f"{input_path.stem}_contradictions.json"
        output_path.write_text(
            json.dumps(contradictions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  Results saved to: {output_path}")
    else:
        print("  No contradictions detected.")
        print("  (This is normal for small datasets or papers on the same topic)")

    print("=" * 60)
    return 0
