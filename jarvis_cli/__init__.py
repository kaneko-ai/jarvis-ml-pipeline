"""JARVIS CLI - Command Line Interface."""

from __future__ import annotations

import argparse
import sys


def main(argv=None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS Research OS - Paper Search & Analysis CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run command ---
    run_parser = subparsers.add_parser("run", help="Run full pipeline")
    run_parser.add_argument("--goal", required=True, help="Task goal")
    run_parser.add_argument("--category", default="generic", help="Task category")

    # --- search command ---
    search_parser = subparsers.add_parser(
        "search", help="Search papers (lightweight, no full pipeline)"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--max", type=int, default=5, dest="max_results",
        help="Max papers (default: 5, max: 20)",
    )
    search_parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output file path",
    )
    search_parser.add_argument(
        "--no-summary", action="store_true",
        help="Skip LLM summary (faster)",
    )
    search_parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output as JSON",
    )
    search_parser.add_argument(
        "--bibtex", action="store_true",
        help="Also save as BibTeX (.bib) file",
    )
    search_parser.add_argument(
        "--provider", type=str, default="gemini",
        choices=["gemini", "codex"],
        help="LLM provider: gemini (default) or codex",
    )
    search_parser.add_argument(
        "--sources", type=str, default=None,
        help="Comma-separated search sources: pubmed,s2,openalex",
    )

    # --- merge command ---
    merge_parser = subparsers.add_parser(
        "merge", help="Merge multiple search result JSONs and deduplicate"
    )
    merge_parser.add_argument(
        "files", nargs="+",
        help="JSON files to merge",
    )
    merge_parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output file path",
    )
    merge_parser.add_argument(
        "--bibtex", action="store_true",
        help="Also generate BibTeX (.bib) file",
    )

    # --- note command ---
    note_parser = subparsers.add_parser(
        "note", help="Generate research note from collected papers"
    )
    note_parser.add_argument(
        "input", help="Merged JSON file",
    )
    note_parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output file path",
    )
    note_parser.add_argument(
        "--provider", type=str, default="codex",
        choices=["gemini", "codex"],
        help="LLM provider: codex (default) or gemini",
    )
    note_parser.add_argument(
        "--obsidian", action="store_true",
        help="Also export each paper to Obsidian Vault",
    )

    # --- citation command ---
    citation_parser = subparsers.add_parser(
        "citation", help="Fetch citation counts from Semantic Scholar"
    )
    citation_parser.add_argument(
        "input", help="Input JSON file",
    )

    # --- prisma command ---
    prisma_parser = subparsers.add_parser(
        "prisma", help="Generate PRISMA 2020 flow diagram"
    )
    prisma_parser.add_argument(
        "files", nargs="+",
        help="Search result JSON files used in the review",
    )
    prisma_parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output file path",
    )

    # --- evidence command --- (T2-1)
    evidence_parser = subparsers.add_parser(
        "evidence", help="Grade CEBM evidence level for each paper"
    )
    evidence_parser.add_argument(
        "input", help="Input JSON file",
    )
    evidence_parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output file path (default: <input>_evidence.json)",
    )
    evidence_parser.add_argument(
        "--use-llm", action="store_true",
        help="Use LLM to re-grade low-confidence papers",
    )

    # --- obsidian-export command --- (T2-2)
    obsidian_parser = subparsers.add_parser(
        "obsidian-export",
        help="Export papers from JSON to Obsidian Vault",
    )
    obsidian_parser.add_argument(
        "input", help="Input JSON file",
    )

    # --- semantic-search command --- (T3-1)
    ss_parser = subparsers.add_parser(
        "semantic-search",
        help="Semantic search within collected papers (BM25 + Sentence Transformers)",
    )
    ss_parser.add_argument(
        "query", help="Search query (e.g. 'immune checkpoint resistance')",
    )
    ss_parser.add_argument(
        "--db", required=True,
        help="Path to paper database JSON file",
    )
    ss_parser.add_argument(
        "--top", type=int, default=10,
        help="Number of top results to show (default: 10)",
    )

    # --- contradict command --- (T3-2)
    contradict_parser = subparsers.add_parser(
        "contradict",
        help="Detect contradictions between papers",
    )
    contradict_parser.add_argument(
        "input", help="Input JSON file",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run":
        return _cmd_run(args)
    if args.command == "search":
        return _cmd_search(args)
    if args.command == "merge":
        return _cmd_merge(args)
    if args.command == "note":
        return _cmd_note(args)
    if args.command == "citation":
        return _cmd_citation(args)
    if args.command == "prisma":
        return _cmd_prisma(args)
    if args.command == "evidence":
        return _cmd_evidence(args)
    if args.command == "obsidian-export":
        return _cmd_obsidian_export(args)
    if args.command == "semantic-search":
        return _cmd_semantic_search(args)
    if args.command == "contradict":
        return _cmd_contradict(args)

    parser.print_help()
    return 0


def _cmd_run(args):
    """run command: full pipeline execution."""
    from jarvis_core.app import run_task

    task_dict = {
        "goal": args.goal,
        "category": args.category,
        "inputs": {"query": args.goal},
    }

    try:
        result = run_task(task_dict)
        print()
        print("=" * 60)
        print(f"  Status : {result.status}")
        print(f"  Log dir: {result.log_dir}")
        print("=" * 60)
        if result.answer:
            print()
            print(result.answer)
        if result.warnings:
            print()
            print("Warnings:")
            for w in result.warnings:
                print(f"  - {w}")
        return 0 if result.status == "success" else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _cmd_search(args):
    """search command: lightweight paper search."""
    from jarvis_cli.search import run_search
    return run_search(args)


def _cmd_merge(args):
    """merge command: merge and deduplicate search results."""
    from jarvis_cli.merge import run_merge
    return run_merge(args)


def _cmd_note(args):
    """note command: generate research note."""
    from jarvis_cli.note import run_note
    result = run_note(args)
    if getattr(args, "obsidian", False) and result == 0:
        print()
        print("Exporting papers to Obsidian Vault...")
        _do_obsidian_export(args.input)
    return result


def _cmd_citation(args):
    """citation command: fetch citation counts."""
    from jarvis_cli.citation import run_citation
    return run_citation(args)


def _cmd_prisma(args):
    """prisma command: generate PRISMA flow diagram."""
    from jarvis_cli.prisma import run_prisma
    return run_prisma(args)


def _cmd_evidence(args):
    """evidence command: grade CEBM evidence levels."""
    from jarvis_cli.evidence import run_evidence
    return run_evidence(args)


def _cmd_obsidian_export(args):
    """obsidian-export command: standalone Obsidian export."""
    _do_obsidian_export(args.input)
    return 0


def _cmd_semantic_search(args):
    """semantic-search command: search within collected papers."""
    from jarvis_cli.semantic_search import run_semantic_search
    return run_semantic_search(args)


def _cmd_contradict(args):
    """contradict command: detect contradictions."""
    from jarvis_cli.contradict import run_contradict
    return run_contradict(args)


def _do_obsidian_export(input_path_str: str):
    """Shared logic for Obsidian export."""
    import json
    from pathlib import Path
    from jarvis_cli.obsidian_export import export_papers_to_obsidian

    input_path = Path(input_path_str)
    if not input_path.exists():
        print(f"  Error: File not found: {input_path}")
        return

    try:
        papers = json.loads(input_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  Error: Could not read JSON: {e}")
        return

    if not isinstance(papers, list):
        print("  Error: JSON root must be an array of papers.")
        return

    try:
        saved = export_papers_to_obsidian(papers)
        print(f"  Exported {len(saved)} papers to Obsidian Vault:")
        for p in saved[:5]:
            print(f"    - {p.name}")
        if len(saved) > 5:
            print(f"    ... and {len(saved) - 5} more")
    except Exception as e:
        print(f"  Error during Obsidian export: {e}")


if __name__ == "__main__":
    sys.exit(main())
