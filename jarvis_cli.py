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
import textwrap


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
            if result["model_saved"]:
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
    from jarvis_core.integrations.ris_bibtex import import_references, references_to_jsonl

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
    from jarvis_core.integrations.ris_bibtex import jsonl_to_references, export_references

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


def cmd_benchmark(args):
    """Run benchmarks."""
    if args.benchmark_command == "mcp":
        from evals.benchmarks.mcp_performance import run_benchmark

        results = run_benchmark(args.output)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print("MCP benchmark completed")
            for key, value in results.items():
                print(f"  {key}: {value}")
    else:
        print("Unknown benchmark command", file=sys.stderr)


def cmd_papers(args):
    """Paper graph features: tree/map3d."""
    if args.papers_command == "tree":
        from jarvis_core.paper_graph import run_tree

        result = run_tree(
            paper_id=args.id,
            depth=args.depth,
            max_per_level=args.max_per_level,
            out=args.out,
            out_run=args.out_run,
        )
    elif args.papers_command == "map3d":
        from jarvis_core.paper_graph import run_map3d

        result = run_map3d(
            paper_id=args.id,
            k_neighbors=args.k,
            seed=args.seed,
            out=args.out,
            out_run=args.out_run,
        )
    else:
        print("Error: Unknown papers command", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {result['run_id']}")
        print(f"Run Dir: {result['run_dir']}")
        print(f"Status: {result['status']}")


def cmd_harvest(args):
    """Harvest watch/work commands."""
    if args.harvest_command == "watch":
        from jarvis_core.harvest import run_watch

        result = run_watch(
            source=args.source,
            since_hours=args.since_hours,
            budget_raw=args.budget,
            out=args.out,
            out_run=args.out_run,
            query=args.query,
        )
    elif args.harvest_command == "work":
        from jarvis_core.harvest import run_work

        result = run_work(
            budget_raw=args.budget,
            out=args.out,
            out_run=args.out_run,
            oa_only=args.oa_only,
        )
    else:
        print("Error: Unknown harvest command", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {result['run_id']}")
        print(f"Run Dir: {result['run_dir']}")
        print(f"Status: {result['status']}")


def cmd_radar(args):
    """R&D radar command."""
    if args.radar_command != "run":
        print("Error: Unknown radar command", file=sys.stderr)
        sys.exit(1)

    from jarvis_core.radar import run_radar

    result = run_radar(
        source=args.source,
        query=args.query,
        since_days=args.since_days,
        out=args.out,
        out_run=args.out_run,
        rss_url=args.rss_url,
        manual_urls_path=args.manual_urls,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {result['run_id']}")
        print(f"Run Dir: {result['run_dir']}")
        print(f"Status: {result['status']}")


def cmd_collect(args):
    """Collector commands."""
    if args.collect_command == "papers":
        from jarvis_core.collector import run_collect_papers

        result = run_collect_papers(
            query=args.query,
            max_items=args.max,
            oa_only=args.oa_only,
            out=args.out,
            out_run=args.out_run,
        )
    elif args.collect_command == "drive-sync":
        from jarvis_core.collector import run_drive_sync

        result = run_drive_sync(
            run_id=args.run_id,
            out=args.out,
            drive_folder=args.drive_folder,
        )
    else:
        print("Error: Unknown collect command", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {result['run_id']}")
        print(f"Run Dir: {result['run_dir']}")
        print(f"Status: {result['status']}")


def cmd_market(args):
    """Market proposal commands."""
    if args.market_command != "propose":
        print("Error: Unknown market command", file=sys.stderr)
        sys.exit(1)
    from jarvis_core.market import run_market_propose

    result = run_market_propose(
        input_run=args.input_run,
        market_data_dir=args.market_data_dir,
        out=args.out,
        out_run=args.out_run,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Run ID: {result['run_id']}")
        print(f"Run Dir: {result['run_dir']}")
        print(f"Status: {result['status']}")


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
            print(
                "Error: Model name required. Example: jarvis model pull llama3.2", file=sys.stderr
            )
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
                    print(
                        f"Quantization: {data.get('details', {}).get('quantization_level', 'N/A')}"
                    )
            else:
                print("Error: Model not found", file=sys.stderr)
                sys.exit(1)
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama", file=sys.stderr)
            sys.exit(1)


def cmd_cache(args):
    """Manage cache (Phase 1: Cache Management CLI)."""
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
            print(
                json.dumps(
                    {
                        "cache_dir": str(cache_dir),
                        "size_bytes": total_size,
                        "size_mb": round(size_mb, 2),
                        "file_count": file_count,
                        "dir_count": dir_count,
                    },
                    indent=2,
                )
            )
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


def cmd_mcp(args):
    """Manage MCP servers and tools."""
    import asyncio
    import json

    from jarvis_core.mcp.hub import MCPHub

    config_path = args.config or "configs/mcp_config.json"
    hub = MCPHub()

    if args.mcp_command == "config":
        print(config_path)
        return

    if Path(config_path).exists():
        hub.register_from_config(config_path)
    else:
        print(f"Warning: MCP config not found at {config_path}", file=sys.stderr)

    if args.mcp_command == "list":
        servers = hub.list_servers()
        tools = hub.list_all_tools()
        if args.json:
            print(json.dumps({"servers": servers, "tools": tools}, ensure_ascii=False, indent=2))
            return
        print("=== MCP Servers ===")
        for server in servers:
            print(
                f"  • {server['name']} ({server['server_type']}) - {server['status']} "
                f"({server['tool_count']} tools)"
            )
        print("\n=== MCP Tools ===")
        for tool in tools:
            print(f"  • {tool['tool']} [{tool['server']}] - {tool['description']}")
        return

    if args.mcp_command == "discover":
        tools = asyncio.run(hub.discover_tools(args.server_name))
        if args.json:
            print(json.dumps([tool.__dict__ for tool in tools], ensure_ascii=False, indent=2))
        else:
            print(f"Discovered {len(tools)} tools from {args.server_name}:")
            for tool in tools:
                print(f"  • {tool.name}: {tool.description}")
        return

    if args.mcp_command == "invoke":
        params = json.loads(args.params) if args.params else {}
        result = asyncio.run(hub.invoke_tool(args.tool_name, params))
        if args.json:
            print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        else:
            status = "success" if result.success else "error"
            print(f"Tool '{result.tool_name}' ({result.server_name}) => {status}")
            if result.data is not None:
                print(json.dumps(result.data, ensure_ascii=False, indent=2))
            if result.error:
                print(f"Error: {result.error}", file=sys.stderr)


def cmd_skills(args):
    """Manage skills definitions and templates."""
    from jarvis_core.skills.engine import SkillsEngine

    engine = SkillsEngine(workspace_path=Path.cwd())

    if args.skills_command == "list":
        skills = engine.list_all_skills()
        if args.json:
            print(json.dumps(skills, ensure_ascii=False, indent=2))
            return
        print("=== Skills ===")
        for skill in skills:
            print(f"  • {skill['name']} ({skill['scope']}) - {skill['description']}")
        return

    if args.skills_command == "match":
        matches = engine.match_skills(args.query)
        if args.json:
            print(json.dumps({"matches": matches}, ensure_ascii=False, indent=2))
            return
        if matches:
            print("Matched skills:")
            for name in matches:
                print(f"  • {name}")
        else:
            print("No matching skills found.")
        return

    if args.skills_command == "show":
        context = engine.get_context_for_llm([args.skill_name])
        if not context:
            print(f"Skill not found: {args.skill_name}", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(
                json.dumps(
                    {"skill": args.skill_name, "context": context}, ensure_ascii=False, indent=2
                )
            )
        else:
            print(context)
        return

    if args.skills_command == "init":
        base_dir = Path.cwd() / ".agent" / "skills" / args.skill_name
        base_dir.mkdir(parents=True, exist_ok=True)
        skill_file = base_dir / "SKILL.md"
        if skill_file.exists() and not args.force:
            print(f"Skill already exists: {skill_file}", file=sys.stderr)
            sys.exit(1)
        template = textwrap.dedent(
            f"""\
            ---
            name: {args.skill_name}
            description: Skill description here.
            triggers:
              - "trigger phrase"
            dependencies: []
            ---
            # {args.skill_name}

            Describe how to use this skill.
            """
        ).strip()
        skill_file.write_text(template + "\n", encoding="utf-8")
        (base_dir / "resources").mkdir(exist_ok=True)
        (base_dir / "scripts").mkdir(exist_ok=True)
        if args.json:
            print(json.dumps({"created": str(skill_file)}, ensure_ascii=False, indent=2))
        else:
            print(f"✅ Created skill template at {skill_file}")
        return

    print("Unknown skills command", file=sys.stderr)
    sys.exit(1)


def cmd_rules(args):
    """Manage rules for global/workspace contexts."""
    from jarvis_core.rules.engine import RulesEngine

    engine = RulesEngine(workspace_path=Path.cwd())

    if args.rules_command == "list":
        rules = engine.list_rules()
        if args.json:
            print(json.dumps(rules, ensure_ascii=False, indent=2))
            return
        print("=== Rules ===")
        for rule in rules:
            print(f"  • {rule['name']} ({rule['scope']})")
        return

    if args.rules_command == "show":
        rules = engine.list_rules()
        rule = next((item for item in rules if item["name"] == args.rule_name), None)
        if not rule:
            print(f"Rule not found: {args.rule_name}", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(
                json.dumps(
                    {"rule": rule["name"], "content": rule["content"]}, ensure_ascii=False, indent=2
                )
            )
        else:
            print(rule["content"])
        return

    if args.rules_command == "init":
        rules_dir = Path.cwd() / ".agent" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        if args.json:
            print(json.dumps({"created": str(rules_dir)}, ensure_ascii=False, indent=2))
        else:
            print(f"✅ Created rules directory at {rules_dir}")
        return

    print("Unknown rules command", file=sys.stderr)
    sys.exit(1)


def cmd_workflows(args):
    """Manage workflows for saved prompts."""
    from jarvis_core.workflows.engine import WorkflowsEngine

    engine = WorkflowsEngine(workspace_path=Path.cwd())

    if args.workflows_command == "list":
        workflows = engine.list_workflows()
        if args.json:
            print(json.dumps(workflows, ensure_ascii=False, indent=2))
            return
        print("=== Workflows ===")
        for workflow in workflows:
            print(f"  • {workflow['name']} ({workflow['scope']}) - {workflow['description']}")
        return

    if args.workflows_command == "show":
        workflow = engine.get_workflow(args.name)
        if not workflow:
            print(f"Workflow not found: {args.name}", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(
                json.dumps(
                    {"workflow": workflow.metadata.name, "content": workflow.content},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(workflow.content)
        return

    if args.workflows_command == "run":
        context = {"args": args.args or []}
        output = engine.execute(args.name, context)
        if args.json:
            print(
                json.dumps({"workflow": args.name, "output": output}, ensure_ascii=False, indent=2)
            )
        else:
            print(output)
        return

    if args.workflows_command == "init":
        workflows_dir = Path.cwd() / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflow_path = workflows_dir / f"{args.name}.md"
        if workflow_path.exists() and not args.force:
            print(f"Workflow already exists: {workflow_path}", file=sys.stderr)
            sys.exit(1)
        template = textwrap.dedent(
            f"""\
            ---
            name: {args.name}
            description: Describe this workflow.
            command: /{args.name}
            ---
            # {args.name}

            1. Describe the first step.
            2. Describe the next step.
            """
        ).strip()
        workflow_path.write_text(template + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps({"created": str(workflow_path)}, ensure_ascii=False, indent=2))
        else:
            print(f"✅ Created workflow template at {workflow_path}")
        return

    print("Unknown workflows command", file=sys.stderr)
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
            print("\n=== Result ===")
            print(f"Status: {result.get('status')}")
            if result.get("warnings"):
                print(f"Warnings: {len(result.get('warnings', []))} items")

        # Show eval and fail reasons
        if eval_summary:
            print("\n=== Evaluation ===")
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
    parser.add_argument(
        "--offline", action="store_true", help="Run in offline mode (no network access)"
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
    ranker_parser.add_argument(
        "--dataset", type=str, required=True, help="Path to golden set JSONL"
    )
    ranker_parser.add_argument("--output", type=str, help="Path to save model (optional)")
    ranker_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === screen command (Sprint 19: Active Learning) ===
    screen_parser = subparsers.add_parser("screen", help="Active learning paper screening")
    screen_parser.add_argument("--input", type=str, required=True, help="Input JSONL with papers")
    screen_parser.add_argument("--output", type=str, required=True, help="Output JSONL with labels")
    screen_parser.add_argument(
        "--batch-size", type=int, default=10, help="Batch size (default: 10)"
    )
    screen_parser.add_argument(
        "--target-recall", type=float, default=0.95, help="Target recall (default: 0.95)"
    )
    screen_parser.add_argument(
        "--budget-ratio", type=float, default=0.3, help="Budget ratio (default: 0.3)"
    )
    screen_parser.add_argument(
        "--initial-samples", type=int, default=20, help="Initial samples (default: 20)"
    )
    screen_parser.add_argument("--auto", action="store_true", help="Auto-label (non-interactive)")
    screen_parser.add_argument("--json", action="store_true", help="Output stats as JSON")

    # === import command (Sprint 20: External Integration) ===
    import_parser = subparsers.add_parser("import", help="Import references from RIS/BibTeX/Zotero")
    import_parser.add_argument(
        "--format",
        type=str,
        required=True,
        choices=["ris", "bibtex", "zotero"],
        help="Import format",
    )
    import_parser.add_argument("--input", type=str, required=True, help="Input file path")
    import_parser.add_argument(
        "--output", type=str, default="papers.jsonl", help="Output JSONL path"
    )
    import_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === export command (Sprint 20: External Integration) ===
    export_parser = subparsers.add_parser("export", help="Export references to RIS/BibTeX/PRISMA")
    export_parser.add_argument(
        "--format",
        type=str,
        required=True,
        choices=["ris", "bibtex", "prisma"],
        help="Export format",
    )
    export_parser.add_argument("--input", type=str, required=True, help="Input JSONL path")
    export_parser.add_argument("--output", type=str, required=True, help="Output file path")
    export_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === model command (Phase 1: Model Management CLI) ===
    model_parser = subparsers.add_parser("model", help="Manage LLM models (Ollama)")
    model_parser.add_argument(
        "action", type=str, choices=["list", "pull", "info"], help="Action to perform"
    )
    model_parser.add_argument("name", type=str, nargs="?", help="Model name (for pull/info)")
    model_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === cache command (Phase 1: Cache Management CLI) ===
    cache_parser = subparsers.add_parser("cache", help="Manage cache")
    cache_parser.add_argument(
        "action", type=str, choices=["stats", "clear", "path"], help="Action to perform"
    )
    cache_parser.add_argument(
        "--force", "-f", action="store_true", help="Force clear without confirmation"
    )
    cache_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # === mcp command ===
    mcp_parser = subparsers.add_parser("mcp", help="Manage MCP servers")
    mcp_parser.add_argument(
        "--config", type=str, default="configs/mcp_config.json", help="Path to MCP config"
    )
    mcp_parser.add_argument("--json", action="store_true", help="Output as JSON")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", help="MCP commands")

    mcp_list_parser = mcp_subparsers.add_parser("list", help="List MCP servers and tools")
    mcp_list_parser.set_defaults(mcp_command="list")

    mcp_discover_parser = mcp_subparsers.add_parser("discover", help="Discover tools from a server")
    mcp_discover_parser.add_argument("server_name", type=str, help="MCP server name")
    mcp_discover_parser.set_defaults(mcp_command="discover")

    mcp_invoke_parser = mcp_subparsers.add_parser("invoke", help="Invoke an MCP tool")
    mcp_invoke_parser.add_argument("tool_name", type=str, help="Tool name to invoke")
    mcp_invoke_parser.add_argument("--params", type=str, help="Tool params as JSON string")
    mcp_invoke_parser.set_defaults(mcp_command="invoke")

    mcp_config_parser = mcp_subparsers.add_parser("config", help="Show MCP config path")
    mcp_config_parser.set_defaults(mcp_command="config")

    # === skills command ===
    skills_parser = subparsers.add_parser("skills", help="Manage skills")
    skills_parser.add_argument("--json", action="store_true", help="Output as JSON")
    skills_subparsers = skills_parser.add_subparsers(dest="skills_command", help="Skills commands")

    skills_list_parser = skills_subparsers.add_parser("list", help="List available skills")
    skills_list_parser.set_defaults(skills_command="list")

    skills_show_parser = skills_subparsers.add_parser("show", help="Show skill details")
    skills_show_parser.add_argument("skill_name", type=str, help="Skill name")
    skills_show_parser.set_defaults(skills_command="show")

    skills_match_parser = skills_subparsers.add_parser("match", help="Match skills to a query")
    skills_match_parser.add_argument("query", type=str, help="Query to match against triggers")
    skills_match_parser.set_defaults(skills_command="match")

    skills_init_parser = skills_subparsers.add_parser("init", help="Create a new skill template")
    skills_init_parser.add_argument("skill_name", type=str, help="New skill name")
    skills_init_parser.add_argument("--force", action="store_true", help="Overwrite existing skill")
    skills_init_parser.set_defaults(skills_command="init")

    # === rules command ===
    rules_parser = subparsers.add_parser("rules", help="Manage rules")
    rules_parser.add_argument("--json", action="store_true", help="Output as JSON")
    rules_subparsers = rules_parser.add_subparsers(dest="rules_command", help="Rules commands")

    rules_list_parser = rules_subparsers.add_parser("list", help="List active rules")
    rules_list_parser.set_defaults(rules_command="list")

    rules_show_parser = rules_subparsers.add_parser("show", help="Show rule content")
    rules_show_parser.add_argument("rule_name", type=str, help="Rule name")
    rules_show_parser.set_defaults(rules_command="show")

    rules_init_parser = rules_subparsers.add_parser(
        "init", help="Initialize workspace rules directory"
    )
    rules_init_parser.set_defaults(rules_command="init")

    # === workflows command ===
    workflows_parser = subparsers.add_parser("workflows", help="Manage workflows")
    workflows_parser.add_argument("--json", action="store_true", help="Output as JSON")
    workflows_subparsers = workflows_parser.add_subparsers(
        dest="workflows_command", help="Workflows commands"
    )

    workflows_list_parser = workflows_subparsers.add_parser("list", help="List workflows")
    workflows_list_parser.set_defaults(workflows_command="list")

    workflows_show_parser = workflows_subparsers.add_parser("show", help="Show workflow content")
    workflows_show_parser.add_argument("name", type=str, help="Workflow name")
    workflows_show_parser.set_defaults(workflows_command="show")

    workflows_run_parser = workflows_subparsers.add_parser("run", help="Run a workflow")
    workflows_run_parser.add_argument("name", type=str, help="Workflow name")
    workflows_run_parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for workflow context"
    )
    workflows_run_parser.set_defaults(workflows_command="run")

    workflows_init_parser = workflows_subparsers.add_parser(
        "init", help="Create a workflow template"
    )
    workflows_init_parser.add_argument("name", type=str, help="Workflow name")
    workflows_init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing workflow"
    )
    workflows_init_parser.set_defaults(workflows_command="init")

    # === papers command ===
    papers_parser = subparsers.add_parser("papers", help="Paper graph features")
    papers_parser.add_argument("--json", action="store_true", help="Output as JSON")
    papers_subparsers = papers_parser.add_subparsers(dest="papers_command", help="Papers commands")

    papers_tree_parser = papers_subparsers.add_parser("tree", help="Build citation tree")
    papers_tree_parser.add_argument("--id", type=str, required=True, help="paper id: doi:/pmid:/arxiv:/s2:")
    papers_tree_parser.add_argument("--depth", type=int, default=2, choices=[1, 2], help="Tree depth")
    papers_tree_parser.add_argument("--max-per-level", type=int, default=50, help="Max refs per level")
    papers_tree_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")
    papers_tree_parser.add_argument("--out-run", type=str, default="auto", help="Run id or auto")

    papers_map_parser = papers_subparsers.add_parser("map3d", help="Build 3D paper map")
    papers_map_parser.add_argument("--id", type=str, required=True, help="paper id: doi:/pmid:/arxiv:/s2:")
    papers_map_parser.add_argument("--k", type=int, default=30, help="Neighbors (10-50)")
    papers_map_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    papers_map_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")
    papers_map_parser.add_argument("--out-run", type=str, default="auto", help="Run id or auto")

    # === harvest command ===
    harvest_parser = subparsers.add_parser("harvest", help="Auto harvest commands")
    harvest_parser.add_argument("--json", action="store_true", help="Output as JSON")
    harvest_subparsers = harvest_parser.add_subparsers(dest="harvest_command", help="Harvest commands")

    harvest_watch_parser = harvest_subparsers.add_parser("watch", help="Watch sources and enqueue")
    harvest_watch_parser.add_argument("--source", type=str, default="pubmed", choices=["pubmed"])
    harvest_watch_parser.add_argument("--query", type=str, default="immunotherapy")
    harvest_watch_parser.add_argument("--since-hours", type=int, default=6)
    harvest_watch_parser.add_argument(
        "--budget", type=str, default="max_items=200,max_minutes=30,max_requests=400"
    )
    harvest_watch_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")
    harvest_watch_parser.add_argument("--out-run", type=str, default="auto", help="Run id or auto")

    harvest_work_parser = harvest_subparsers.add_parser("work", help="Process queued harvest items")
    harvest_work_parser.add_argument(
        "--budget", type=str, default="max_items=200,max_minutes=30,max_requests=400"
    )
    harvest_work_parser.add_argument("--oa-only", type=lambda v: str(v).lower() == "true", default=True)
    harvest_work_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")
    harvest_work_parser.add_argument("--out-run", type=str, default="auto", help="Run id or auto")

    # === radar command ===
    radar_parser = subparsers.add_parser("radar", help="R&D radar commands")
    radar_parser.add_argument("--json", action="store_true", help="Output as JSON")
    radar_subparsers = radar_parser.add_subparsers(dest="radar_command", help="Radar commands")

    radar_run_parser = radar_subparsers.add_parser("run", help="Run radar collection and proposals")
    radar_run_parser.add_argument("--source", type=str, default="arxiv", choices=["arxiv", "rss", "all"])
    radar_run_parser.add_argument("--query", type=str, default="immunometabolism PD-1")
    radar_run_parser.add_argument("--since-days", type=int, default=2)
    radar_run_parser.add_argument("--rss-url", type=str, default=None)
    radar_run_parser.add_argument("--manual-urls", type=str, default=None)
    radar_run_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")
    radar_run_parser.add_argument("--out-run", type=str, default="auto", help="Run id or auto")

    # === collect command ===
    collect_parser = subparsers.add_parser("collect", help="Collector commands")
    collect_parser.add_argument("--json", action="store_true", help="Output as JSON")
    collect_subparsers = collect_parser.add_subparsers(dest="collect_command", help="Collect commands")

    collect_papers_parser = collect_subparsers.add_parser("papers", help="Collect papers metadata")
    collect_papers_parser.add_argument("--query", type=str, required=True)
    collect_papers_parser.add_argument("--max", type=int, default=50)
    collect_papers_parser.add_argument("--oa-only", type=lambda v: str(v).lower() == "true", default=True)
    collect_papers_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")
    collect_papers_parser.add_argument("--out-run", type=str, default="auto", help="Run id or auto")

    collect_drive_parser = collect_subparsers.add_parser("drive-sync", help="Sync collected run to drive")
    collect_drive_parser.add_argument("--run-id", type=str, required=True)
    collect_drive_parser.add_argument("--drive-folder", type=str, default=None)
    collect_drive_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")

    # === market command ===
    market_parser = subparsers.add_parser("market", help="Market proposal commands")
    market_parser.add_argument("--json", action="store_true", help="Output as JSON")
    market_subparsers = market_parser.add_subparsers(dest="market_command", help="Market commands")

    market_propose_parser = market_subparsers.add_parser("propose", help="Generate market proposals")
    market_propose_parser.add_argument("--input-run", type=str, required=True)
    market_propose_parser.add_argument("--market-data-dir", type=str, default=None)
    market_propose_parser.add_argument("--out", type=str, default="logs/runs", help="Base output directory")
    market_propose_parser.add_argument("--out-run", type=str, default="auto", help="Run id or auto")

    # === sync command ===
    sync_parser = subparsers.add_parser("sync", help="Process pending sync queue items")

    # === sync-status command ===
    sync_status_parser = subparsers.add_parser("sync-status", help="Show sync queue status")

    # === benchmark command ===
    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    benchmark_parser.add_argument("--json", action="store_true", help="Output as JSON")
    benchmark_parser.add_argument("--output", type=str, default="results/mcp_benchmark.json")
    benchmark_subparsers = benchmark_parser.add_subparsers(
        dest="benchmark_command", help="Benchmark commands"
    )
    benchmark_mcp_parser = benchmark_subparsers.add_parser(
        "mcp", help="Benchmark MCP Hub performance"
    )
    benchmark_mcp_parser.set_defaults(benchmark_command="mcp")

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
    elif args.command == "mcp":
        cmd_mcp(args)
    elif args.command == "skills":
        cmd_skills(args)
    elif args.command == "rules":
        cmd_rules(args)
    elif args.command == "workflows":
        cmd_workflows(args)
    elif args.command == "papers":
        cmd_papers(args)
    elif args.command == "harvest":
        cmd_harvest(args)
    elif args.command == "radar":
        cmd_radar(args)
    elif args.command == "collect":
        cmd_collect(args)
    elif args.command == "market":
        cmd_market(args)
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
    elif args.command == "benchmark":
        cmd_benchmark(args)


if __name__ == "__main__":
    main()
