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
import os
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


def cmd_import(args):
    """Import references from RIS/BibTeX/Zotero (Sprint 20)."""
    from pathlib import Path
    from jarvis_core.integrations.ris_bibtex import (
        import_references, references_to_jsonl
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.format == "zotero":
            from jarvis_core.plugins.zotero_integration import ZoteroClient
            client = ZoteroClient()
            refs = client.get_all_items()
        else:
            refs = import_references(input_path, args.format)
        
        references_to_jsonl(refs, output_path)
        
        if args.json:
            print(json.dumps({"imported": len(refs), "output": str(output_path)}))
        else:
            print(f"✅ Imported {len(refs)} references to {output_path}")
    except Exception as e:
        print(f"Error importing: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    """Export references to RIS/BibTeX/PRISMA (Sprint 20)."""
    from pathlib import Path
    from jarvis_core.integrations.ris_bibtex import (
        jsonl_to_references, export_references
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        refs = jsonl_to_references(input_path)
        
        if args.format == "prisma":
            from jarvis_core.prisma import PRISMAData, generate_prisma_flow
            data = PRISMAData(
                records_from_databases=len(refs),
                studies_included=len([r for r in refs if r.abstract]),
            )
            content = generate_prisma_flow(data, format="svg")
            output_path.write_text(content, encoding="utf-8")
        else:
            export_references(refs, output_path, args.format)
        
        if args.json:
            print(json.dumps({"exported": len(refs), "output": str(output_path)}))
        else:
            print(f"✅ Exported {len(refs)} references to {output_path}")
    except Exception as e:
        print(f"Error exporting: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_model(args):
    """Manage LLM models (Phase 1: Model Management CLI)."""
    import os
    import requests
    
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    
    if args.action == "list":
        try:
            resp = requests.get(f"{ollama_url}/api/tags", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                
                if args.json:
                    print(json.dumps({"models": models}, indent=2))
                else:
                    print("=== Available Models ===")
                    if models:
                        for m in models:
                            name = m.get("name", "unknown")
                            size = m.get("size", 0) / (1024**3)
                            print(f"  • {name} ({size:.1f} GB)")
                    else:
                        print("  No models installed. Use 'jarvis model pull <name>' to download.")
            else:
                print(f"Error: Ollama returned {resp.status_code}", file=sys.stderr)
                sys.exit(1)
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama. Is it running?", file=sys.stderr)
            print(f"  URL: {ollama_url}", file=sys.stderr)
            print("  Start with: ollama serve", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == "pull":
        if not args.name:
            print("Error: Model name required. Example: jarvis model pull llama3.2", file=sys.stderr)
            sys.exit(1)
        
        print(f"Pulling model '{args.name}'...")
        try:
            resp = requests.post(
                f"{ollama_url}/api/pull",
                json={"name": args.name, "stream": False},
                timeout=600,  # 10 minutes for large models
            )
            if resp.status_code == 200:
                print(f"✅ Model '{args.name}' pulled successfully")
            else:
                print(f"Error: {resp.text}", file=sys.stderr)
                sys.exit(1)
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == "info":
        if not args.name:
            print("Error: Model name required", file=sys.stderr)
            sys.exit(1)
        
        try:
            resp = requests.post(
                f"{ollama_url}/api/show",
                json={"name": args.name},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    print(f"=== Model: {args.name} ===")
                    print(f"Family: {data.get('details', {}).get('family', 'N/A')}")
                    print(f"Parameters: {data.get('details', {}).get('parameter_size', 'N/A')}")
                    print(f"Quantization: {data.get('details', {}).get('quantization_level', 'N/A')}")
            else:
                print(f"Error: Model not found", file=sys.stderr)
                sys.exit(1)
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama", file=sys.stderr)
            sys.exit(1)


def cmd_cache(args):
    """Manage cache (Phase 1: Cache Management CLI)."""
    from pathlib import Path
    import os
    import shutil
    
    cache_dir = Path(os.environ.get("JARVIS_CACHE_DIR", Path.home() / ".jarvis" / "cache"))
    
    if args.action == "stats":
        if not cache_dir.exists():
            print("Cache directory does not exist yet.")
            return
        
        # Calculate stats
        total_size = 0
        file_count = 0
        dir_count = 0
        
        for item in cache_dir.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
            elif item.is_dir():
                dir_count += 1
        
        size_mb = total_size / (1024 * 1024)
        
        if args.json:
            print(json.dumps({
                "cache_dir": str(cache_dir),
                "size_bytes": total_size,
                "size_mb": round(size_mb, 2),
                "file_count": file_count,
                "dir_count": dir_count,
            }, indent=2))
        else:
            print("=== Cache Statistics ===")
            print(f"Location: {cache_dir}")
            print(f"Size: {size_mb:.2f} MB")
            print(f"Files: {file_count}")
            print(f"Directories: {dir_count}")
    
    elif args.action == "clear":
        if not cache_dir.exists():
            print("Cache directory does not exist.")
            return
        
        if not args.force:
            confirm = input(f"Clear all cache at {cache_dir}? [y/N] ").strip().lower()
            if confirm != "y":
                print("Cancelled.")
                return
        
        try:
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Cache cleared: {cache_dir}")
        except Exception as e:
            print(f"Error clearing cache: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == "path":
        print(cache_dir)


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
    # Global options
    parser.add_argument("--offline", action="store_true", help="Run in offline mode (no network access)")
    
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

    # === screen command (Sprint 19: Active Learning) ===
    screen_parser = subparsers.add_parser("screen", help="Active learning paper screening")
    screen_parser.add_argument("--input", type=str, required=True, help="Input JSONL with papers")
    screen_parser.add_argument("--output", type=str, required=True, help="Output JSONL with labels")
    screen_parser.add_argument("--batch-size", type=int, default=10, help="Batch size (default: 10)")
    screen_parser.add_argument("--target-recall", type=float, default=0.95, help="Target recall (default: 0.95)")
    screen_parser.add_argument("--budget-ratio", type=float, default=0.3, help="Budget ratio (default: 0.3)")
    screen_parser.add_argument("--initial-samples", type=int, default=20, help="Initial samples (default: 20)")
    screen_parser.add_argument("--auto", action="store_true", help="Auto-label (non-interactive)")
    screen_parser.add_argument("--json", action="store_true", help="Output stats as JSON")

    # === import command (Sprint 20: External Integration) ===
    import_parser = subparsers.add_parser("import", help="Import references from RIS/BibTeX/Zotero")
    import_parser.add_argument("--format", type=str, required=True, choices=["ris", "bibtex", "zotero"], help="Import format")
    import_parser.add_argument("--input", type=str, required=True, help="Input file path")
    import_parser.add_argument("--output", type=str, default="papers.jsonl", help="Output JSONL path")
    import_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === export command (Sprint 20: External Integration) ===
    export_parser = subparsers.add_parser("export", help="Export references to RIS/BibTeX/PRISMA")
    export_parser.add_argument("--format", type=str, required=True, choices=["ris", "bibtex", "prisma"], help="Export format")
    export_parser.add_argument("--input", type=str, required=True, help="Input JSONL path")
    export_parser.add_argument("--output", type=str, required=True, help="Output file path")
    export_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === model command (Phase 1: Model Management CLI) ===
    model_parser = subparsers.add_parser("model", help="Manage LLM models (Ollama)")
    model_parser.add_argument("action", type=str, choices=["list", "pull", "info"], help="Action to perform")
    model_parser.add_argument("name", type=str, nargs="?", help="Model name (for pull/info)")
    model_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === cache command (Phase 1: Cache Management CLI) ===
    cache_parser = subparsers.add_parser("cache", help="Manage cache")
    cache_parser.add_argument("action", type=str, choices=["stats", "clear", "path"], help="Action to perform")
    cache_parser.add_argument("--force", "-f", action="store_true", help="Force clear without confirmation")
    cache_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === sync command ===
    sync_parser = subparsers.add_parser("sync", help="Process pending sync queue items")
    
    # === sync-status command ===
    sync_status_parser = subparsers.add_parser("sync-status", help="Show sync queue status")

    args = parser.parse_args()

    # Handle global flags
    offline_mode = args.offline or os.environ.get("JARVIS_OFFLINE", "").lower() == "true"
    if offline_mode:
        from jarvis_core.network.degradation import DegradationManager, DegradationLevel
        from jarvis_core.ui.status import get_status_banner
        
        manager = DegradationManager.get_instance()
        manager.set_level(DegradationLevel.OFFLINE)
        
        # Display banner if command is executed
        banner = get_status_banner()
        if banner and args.command:
             # Use stderr or standard print
             print(f"\n{banner}\n", file=sys.stderr)

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
    elif args.command == "screen":
        from jarvis_core.active_learning.cli import cmd_screen
        cmd_screen(args)
    elif args.command == "import":
        cmd_import(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "model":
        cmd_model(args)
    elif args.command == "cache":
        cmd_cache(args)
    elif args.command == "sync":
        from jarvis_core.sync.manager import SyncQueueManager
        manager = SyncQueueManager()
        results = manager.process_queue()
        completed = sum(1 for r in results if r.status.value == "completed")
        failed = sum(1 for r in results if r.status.value == "failed")
        print(f"Sync complete: {completed} succeeded, {failed} failed")
    elif args.command == "sync-status":
        from jarvis_core.sync.manager import SyncQueueManager
        manager = SyncQueueManager()
        status = manager.get_queue_status()
        print("Sync Queue Status:")
        for k, v in status.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
