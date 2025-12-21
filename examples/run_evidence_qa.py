#!/usr/bin/env python
"""Example: Evidence-based QA with PDF or URL inputs.

This script demonstrates the Evidence QA pipeline:
1. Ingest sources (PDF/URL)
2. Retrieve relevant evidence
3. Generate answer with citations
4. Validate citations

Usage:
    python examples/run_evidence_qa.py --pdf tests/fixtures/sample.pdf --q "What is on page 1?"
    python examples/run_evidence_qa.py --url https://example.com --q "What is this about?"
    python examples/run_evidence_qa.py --pdf paper.pdf --q "..." --out ./output
    python examples/run_evidence_qa.py --pdf paper.pdf --q "..." --json
    python examples/run_evidence_qa.py --pdf paper.pdf --q "..." --bibtex
    python examples/run_evidence_qa.py --pdf paper.pdf --q "..." --ris

Requirements:
    Set GEMINI_API_KEY environment variable, or use OLLAMA with LLM_PROVIDER=ollama
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.evidence_qa import (
    run_evidence_qa,
    run_evidence_qa_result,
    get_evidence_store_for_bundle,
)


def main():
    parser = argparse.ArgumentParser(
        description="Evidence-based QA with Jarvis"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        action="append",
        default=[],
        help="PDF file path(s) to use as evidence",
    )
    parser.add_argument(
        "--url",
        type=str,
        action="append",
        default=[],
        help="URL(s) to use as evidence",
    )
    parser.add_argument(
        "--q", "--query",
        type=str,
        required=True,
        dest="query",
        help="Question to answer",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="generic",
        help="Task category (default: generic)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output directory for evidence bundle",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output result as JSON to stdout",
    )
    parser.add_argument(
        "--bibtex",
        action="store_true",
        help="Output BibTeX references to stdout",
    )
    parser.add_argument(
        "--ris",
        action="store_true",
        help="Output RIS references to stdout (Zotero/EndNote)",
    )
    parser.add_argument(
        "--claims-md",
        action="store_true",
        dest="claims_md",
        help="Output claims as Markdown to stdout",
    )
    parser.add_argument(
        "--claims-json",
        action="store_true",
        dest="claims_json",
        help="Output claims as JSON to stdout",
    )
    parser.add_argument(
        "--slides-outline",
        action="store_true",
        dest="slides_outline",
        help="Output PPTX-style slide outline to stdout",
    )

    args = parser.parse_args()

    # Collect all inputs
    inputs = args.pdf + args.url

    if not inputs:
        print("Error: At least one --pdf or --url is required", file=sys.stderr)
        sys.exit(1)

    print(f"Query: {args.query}", file=sys.stderr)
    print(f"Sources: {inputs}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    try:
        # Get structured result
        result = run_evidence_qa_result(
            query=args.query,
            inputs=inputs,
            category=args.category,
        )

        # BibTeX output
        if args.bibtex:
            from jarvis_core.reference import extract_references
            from jarvis_core.bibtex import export_bibtex

            refs = extract_references(result.citations)
            print(export_bibtex(refs))
            return

        # RIS output
        if args.ris:
            from jarvis_core.reference import extract_references
            from jarvis_core.ris import export_ris

            refs = extract_references(result.citations)
            print(export_ris(refs))
            return

        # Claims Markdown output
        if args.claims_md:
            from jarvis_core.reference import extract_references
            from jarvis_core.claim_export import export_claims_markdown

            if result.claims:
                refs = extract_references(result.citations)
                print(export_claims_markdown(result.claims, refs))
            else:
                print("No claims available")
            return

        # Claims JSON output
        if args.claims_json:
            from jarvis_core.reference import extract_references
            from jarvis_core.claim_export import export_claims_json

            if result.claims:
                refs = extract_references(result.citations)
                print(export_claims_json(result.claims, refs))
            else:
                print("{}")
            return

        # Slides outline output
        if args.slides_outline:
            from jarvis_core.reference import extract_references
            from jarvis_core.claim_export import export_claims_pptx_outline

            if result.claims:
                refs = extract_references(result.citations)
                print(export_claims_pptx_outline(result.claims, refs, args.query))
            else:
                print("No claims available for slides")
            return

        # Output as JSON if requested
        if args.as_json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            print("Answer:")
            print(result.answer)
            print()
            print(f"Status: {result.status}")
            print(f"Citations: {len(result.citations)}")

        # Export bundle if output directory specified
        if args.out:
            from jarvis_core.bundle import export_evidence_bundle

            # Get the evidence store
            store = get_evidence_store_for_bundle(inputs)

            bundle_path = export_evidence_bundle(result, store, args.out)
            print(f"\nBundle exported to: {bundle_path}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


