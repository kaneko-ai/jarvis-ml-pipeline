"""jarvis evidence - CEBM Evidence Level classification (v2 T2-1)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def run_evidence(args):
    """evidence command main logic."""
    from jarvis_core.evidence import grade_evidence

    input_path = Path(args.input)
    use_llm = getattr(args, "use_llm", False)

    # 1. Read input file
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        raw_text = input_path.read_text(encoding="utf-8")
        papers = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(papers, list):
        print("Error: JSON root must be an array of papers.", file=sys.stderr)
        return 1

    total = len(papers)
    print(f"Grading evidence for {total} papers...")
    if use_llm:
        print("  Mode: Hybrid (rule-based first, LLM for low-confidence papers)")
    else:
        print("  Mode: Rule-based only (fast, no API calls)")
    print()

    # 2. Grade each paper
    graded_count = 0
    skipped_count = 0
    llm_retry_count = 0

    for i, paper in enumerate(papers, 1):
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")

        if not title and not abstract:
            skipped_count += 1
            paper["evidence_level"] = "unknown"
            paper["evidence_confidence"] = 0.0
            paper["study_type"] = "unknown"
            paper["evidence_description"] = "Unknown (no title/abstract)"
            continue

        grade = grade_evidence(
            title=title,
            abstract=abstract,
            use_llm=False,
        )

        if use_llm and grade.confidence < 0.6:
            try:
                grade_llm = grade_evidence(
                    title=title,
                    abstract=abstract,
                    use_llm=True,
                )
                if grade_llm.confidence > grade.confidence:
                    grade = grade_llm
                llm_retry_count += 1
            except Exception as e:
                print(f"  [{i}/{total}] LLM retry failed: {e}")

        paper["evidence_level"] = grade.level.value
        paper["evidence_confidence"] = round(grade.confidence, 3)
        paper["study_type"] = grade.study_type.value
        paper["evidence_description"] = grade.level.description

        graded_count += 1

        if i % 10 == 0 or i == total:
            short_title = title[:60] + "..." if len(title) > 60 else title
            print(f"  [{i}/{total}] {short_title}")
            print(
                f"           Level: {grade.level.value} "
                f"({grade.level.description})  "
                f"Confidence: {grade.confidence:.2f}"
            )

    # 3. Save results
    print()
    output_path = _get_output_path(args, input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(papers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Results saved to: {output_path}")

    # 4. Print summary
    print()
    print(f"Graded: {graded_count}/{total} papers")
    if skipped_count > 0:
        print(f"Skipped: {skipped_count} papers (no title/abstract)")
    if llm_retry_count > 0:
        print(f"LLM re-graded: {llm_retry_count} papers")

    _print_summary(papers)

    return 0


def _get_output_path(args, input_path):
    """Determine output file path."""
    if getattr(args, "output", None):
        return Path(args.output)
    stem = input_path.stem
    return input_path.parent / f"{stem}_evidence.json"


def _print_summary(papers):
    """Print evidence level distribution summary."""
    levels = [p.get("evidence_level", "unknown") for p in papers]
    counter = Counter(levels)

    level_order = [
        "1a", "1b", "1c",
        "2a", "2b", "2c",
        "3a", "3b",
        "4",
        "5",
        "unknown",
    ]

    level_labels = {
        "1a": "Systematic Review (RCTs)",
        "1b": "Individual RCT",
        "1c": "All or None",
        "2a": "Systematic Review (Cohort)",
        "2b": "Individual Cohort Study",
        "2c": "Outcomes Research",
        "3a": "Systematic Review (Case-Control)",
        "3b": "Individual Case-Control",
        "4": "Case Series",
        "5": "Expert Opinion",
        "unknown": "Unknown",
    }

    print()
    print("=" * 55)
    print("  Evidence Level Distribution")
    print("=" * 55)

    for level in level_order:
        count = counter.get(level, 0)
        if count > 0:
            bar = "#" * count
            label = level_labels.get(level, "")
            print(f"  {level:>7s} : {count:>3d}  {bar}  {label}")

    total_str = "Total"
    total_count = len(papers)
    print(f"  {total_str:>7s} : {total_count:>3d}")
    print("=" * 55)
