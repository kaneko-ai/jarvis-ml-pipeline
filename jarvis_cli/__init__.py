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
    search_parser.add_argument("query", help="Search query (e.g. 'PD-1')")
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

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run":
        return _cmd_run(args)

    if args.command == "search":
        return _cmd_search(args)

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


if __name__ == "__main__":
    sys.exit(main())