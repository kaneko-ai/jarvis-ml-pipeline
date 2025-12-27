#!/usr/bin/env python
"""JARVIS CLI.

Per RP-09/RP-19, this provides unified CLI with subcommands:
- run: Execute a task
- build-index: Build search index
- show-run: Show run summary
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def cmd_run(args):
    """Execute a task via unified pipeline (per DEC-006)."""
    from jarvis_core.app import run_task

    # Build task dict
    if args.task_file:
        with open(args.task_file, "r", encoding="utf-8") as f:
            task_dict = json.load(f)
    elif args.goal:
        task_dict = {
            "goal": args.goal,
            "category": args.category,
        }
    else:
        print("Error: Provide either --task-file or --goal", file=sys.stderr)
        sys.exit(1)

    # Build config dict with pipeline info
    config_dict = None
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
    else:
        config_dict = {}

    # Add pipeline path if specified
    if args.pipeline:
        config_dict["pipeline"] = args.pipeline

    result = run_task(task_dict, config_dict)

    # Output
    if args.json:
        output = {
            "run_id": result.run_id,
            "log_dir": result.log_dir,
            "status": result.status,
            "answer": result.answer,
            "citations": result.citations,
            "warnings": result.warnings,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {result.run_id}")
        print(f"Log Dir: {result.log_dir}")
        print(f"Status: {result.status}")
        print()
        print("=== Answer ===")
        print(result.answer)

        if result.citations:
            print()
            print(f"=== Citations ({len(result.citations)}) ===")
            for c in result.citations[:5]:
                if isinstance(c, dict):
                    print(f"  - {c.get('source', 'unknown')}: {c.get('locator', '')}")

        if result.warnings:
            print()
            print("=== Warnings ===")
            for w in result.warnings:
                print(f"  - {w}")


def cmd_build_index(args):
    """Build search index from papers."""
    from jarvis_core.index_builder import build_index

    result = build_index(
        query=args.query,
        source=args.source,
        output_dir=args.out,
        max_papers=args.max_papers,
        local_pdf_dir=args.local_pdf_dir,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Index Version: {result['index_version']}")
        print(f"Documents: {result['doc_count']}")
        print(f"Output: {result['output_dir']}")
        if result.get("errors"):
            print(f"Errors: {len(result['errors'])}")


def cmd_train_ranker(args):
    """Train LightGBM ranker on golden dataset (Phase 2)."""
    from pathlib import Path
    from jarvis_core.ranking.lgbm_ranker import LGBMRanker

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Error: Dataset not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else None

    ranker = LGBMRanker()
    try:
        result = ranker.train(dataset_path, output_path)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"✅ Ranker trained on {result['num_papers']} papers")
            print(f"Features: {', '.join(result['feature_names'])}")
            if result['model_saved']:
                print(f"Model saved to: {result['model_saved']}")
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Install LightGBM: pip install lightgbm", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error training ranker: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_show_run(args):
    """Show run summary with fail reasons and missing artifacts (per DEC-006)."""
    from jarvis_core.storage import RunStore

    if args.run_id:
        store = RunStore(args.run_id)
    else:
        store = RunStore.get_latest()
        if not store:
            print("No runs found", file=sys.stderr)
            sys.exit(1)

    summary = store.get_summary()
    config = store.load_config()
    result = store.load_result()
    eval_summary = store.load_eval()

    if args.json:
        output = {
            "summary": summary,
            "config": config,
            "result": result,
            "eval": eval_summary,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {summary['run_id']}")
        print(f"Log Dir: {summary['run_dir']}")
        print(f"Contract Valid: {summary['contract_valid']}")

        # Show artifact status (10-file contract per DEC-006)
        print("\n=== Artifacts (10-file contract) ===")
        artifact_status = [
            ("input.json", summary.get("has_input", False)),
            ("run_config.json", summary.get("has_config", False)),
            ("papers.jsonl", summary.get("has_papers", False)),
            ("claims.jsonl", summary.get("has_claims", False)),
            ("evidence.jsonl", summary.get("has_evidence", False)),
            ("scores.json", summary.get("has_scores", False)),
            ("result.json", summary.get("has_result", False)),
            ("eval_summary.json", summary.get("has_eval", False)),
            ("warnings.jsonl", summary.get("has_warnings", False)),
            ("report.md", summary.get("has_report", False)),
        ]
        for name, exists in artifact_status:
            status = "✓" if exists else "✗"
            print(f"  {status} {name}")

        # Show missing artifacts
        if summary.get("missing_artifacts"):
            print("\n=== Missing Artifacts ===")
            for missing in summary["missing_artifacts"]:
                print(f"  - {missing}")

        # Show config
        if config:
            print(f"\nConfig: pipeline={config.get('pipeline', 'N/A')}, seed={config.get('seed')}")

        # Show result status
        if result:
            print(f"\n=== Result ===")
            print(f"Status: {result.get('status')}")
            if result.get("warnings"):
                print(f"Warnings: {len(result.get('warnings', []))} items")

        # Show eval and fail reasons
        if eval_summary:
            print(f"\n=== Evaluation ===")
            print(f"Gate Passed: {eval_summary.get('gate_passed', 'N/A')}")

            fail_reasons = eval_summary.get("fail_reasons", [])
            if fail_reasons:
                print("\n=== Fail Reasons ===")
                for reason in fail_reasons:
                    if isinstance(reason, dict):
                        print(f"  - [{reason.get('code', 'UNKNOWN')}] {reason.get('msg', '')}")
                    else:
                        print(f"  - {reason}")


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS Research OS CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # === run command ===
    run_parser = subparsers.add_parser("run", help="Execute a task")
    run_parser.add_argument("--task-file", type=str, help="Path to task JSON file")
    run_parser.add_argument("--goal", type=str, help="Task goal")
    run_parser.add_argument(
        "--category",
        type=str,
        default="generic",
        choices=["paper_survey", "thesis", "job_hunting", "generic"],
    )
    run_parser.add_argument("--config", type=str, help="Path to run config JSON")
    run_parser.add_argument(
        "--pipeline",
        type=str,
        default="configs/pipelines/e2e_oa10.yml",
        help="Path to pipeline YAML (default: e2e_oa10.yml)",
    )
    run_parser.add_argument("--out", type=str, default="logs/runs", help="Output directory")
    run_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === build-index command ===
    build_parser = subparsers.add_parser("build-index", help="Build search index")
    build_parser.add_argument("--query", type=str, help="PubMed query (e.g., 'CD73 immunotherapy')")
    build_parser.add_argument("--source", type=str, default="pubmed", choices=["pubmed", "local"])
    build_parser.add_argument("--out", type=str, default="data/index", help="Output directory")
    build_parser.add_argument("--max-papers", type=int, default=50, help="Max papers to fetch")
    build_parser.add_argument("--local-pdf-dir", type=str, help="Local PDF directory")
    build_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === show-run command ===
    show_parser = subparsers.add_parser("show-run", help="Show run summary")
    show_parser.add_argument("--run-id", type=str, help="Run ID (default: latest)")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === train-ranker command (Phase 2) ===
    ranker_parser = subparsers.add_parser("train-ranker", help="Train LightGBM ranker (Phase 2)")
    ranker_parser.add_argument("--dataset", type=str, required=True, help="Path to golden set JSONL")
    ranker_parser.add_argument("--output", type=str, help="Path to save model (optional)")
    ranker_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Legacy mode: if no subcommand but --goal provided
    if not args.command:
        if hasattr(args, "goal") and args.goal:
            # Fallback to run command
            cmd_run(args)
        else:
            parser.print_help()
            sys.exit(0)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "build-index":
        cmd_build_index(args)
    elif args.command == "show-run":
        cmd_show_run(args)
    elif args.command == "train-ranker":
        cmd_train_ranker(args)


if __name__ == "__main__":
    main()
