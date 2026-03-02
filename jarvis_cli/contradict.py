"""jarvis contradict - Contradiction detection between papers (T3-2 + B-2).

Compares all pairs of paper abstracts and detects potential contradictions.
B-2: Added --use-llm flag for Gemini-based semantic contradiction detection.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


def run_contradict(args):
    """contradict command main logic."""
    from jarvis_core.contradiction.detector import ContradictionDetector
    from jarvis_core.contradiction.schema import Claim

    input_path = Path(args.input)
    use_llm = getattr(args, "use_llm", False)

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
    print(f"  Method: {'LLM (Gemini)' if use_llm else 'Heuristic (antonym + overlap)'}")
    print()

    detector = ContradictionDetector(use_llm=use_llm)
    contradictions = []
    pair_count = 0

    for i in range(n):
        for j in range(i + 1, n):
            pair_count += 1
            paper_a = papers_with_abstract[i]
            paper_b = papers_with_abstract[j]

            title_a = paper_a.get("title", f"Paper_{i}")[:50]
            print(f"  [{pair_count}/{total_pairs}] {title_a}...")

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
            except Exception as e:
                print(f"    Warning: Detection failed: {e}")
                continue

            if result.is_contradictory:
                contradictions.append({
                    "paper_a": paper_a.get("title", ""),
                    "paper_b": paper_b.get("title", ""),
                    "score": round(result.confidence, 3),
                    "type": result.contradiction_type.value,
                    "explanation": result.explanation,
                })

            if use_llm:
                time.sleep(4)  # Gemini rate limit

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
            print(f"  --- #{idx} (score: {c['score']}, type: {c['type']}) ---")
            print(f"    A: {title_a}")
            print(f"    B: {title_b}")
            if c.get("explanation"):
                print(f"    Reason: {c['explanation']}")
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
