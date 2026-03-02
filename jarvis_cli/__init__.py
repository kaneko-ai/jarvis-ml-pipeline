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

    # --- run ---
    run_p = subparsers.add_parser("run", help="Run full pipeline")
    run_p.add_argument("--goal", required=True)
    run_p.add_argument("--category", default="generic")

    # --- search ---
    s_p = subparsers.add_parser("search", help="Search papers")
    s_p.add_argument("query")
    s_p.add_argument("--max", type=int, default=5, dest="max_results")
    s_p.add_argument("--output", "-o", type=str, default=None)
    s_p.add_argument("--no-summary", action="store_true")
    s_p.add_argument("--json", action="store_true", dest="json_output")
    s_p.add_argument("--bibtex", action="store_true")
    s_p.add_argument("--provider", default="gemini", choices=["gemini", "codex"])
    s_p.add_argument("--sources", type=str, default=None,
                     help="Comma-separated: pubmed,s2,openalex,arxiv,crossref")

    # --- merge ---
    m_p = subparsers.add_parser("merge", help="Merge JSON results")
    m_p.add_argument("files", nargs="+")
    m_p.add_argument("--output", "-o", type=str, default=None)
    m_p.add_argument("--bibtex", action="store_true")

    # --- note ---
    n_p = subparsers.add_parser("note", help="Generate research note")
    n_p.add_argument("input")
    n_p.add_argument("--output", "-o", type=str, default=None)
    n_p.add_argument("--provider", default="codex", choices=["gemini", "codex"])
    n_p.add_argument("--obsidian", action="store_true")

    # --- citation ---
    c_p = subparsers.add_parser("citation", help="Fetch citation counts")
    c_p.add_argument("input")

    # --- citation-stance (B-1) ---
    cs_p = subparsers.add_parser("citation-stance", help="Classify citation stance between papers")
    cs_p.add_argument("input")
    cs_p.add_argument("--no-llm", action="store_true",
                       help="Use keyword heuristic only (no Gemini)")

    # --- prisma ---
    pr_p = subparsers.add_parser("prisma", help="Generate PRISMA diagram")
    pr_p.add_argument("files", nargs="+")
    pr_p.add_argument("--output", "-o", type=str, default=None)

    # --- evidence (T2-1) ---
    ev_p = subparsers.add_parser("evidence", help="Grade CEBM evidence level")
    ev_p.add_argument("input")
    ev_p.add_argument("--output", "-o", type=str, default=None)
    ev_p.add_argument("--use-llm", action="store_true")

    # --- score (B-3) ---
    sc_p = subparsers.add_parser("score", help="Calculate paper quality scores")
    sc_p.add_argument("input")
    sc_p.add_argument("--output", "-o", type=str, default=None)

    # --- screen (B-4) ---
    sr_p = subparsers.add_parser("screen", help="Active learning paper screening")
    sr_p.add_argument("input", help="JSON file with papers to screen")
    sr_p.add_argument("--auto", action="store_true",
                       help="Auto-label using keywords (no human input)")
    sr_p.add_argument("--batch-size", type=int, default=5,
                       help="Papers per iteration (default: 5)")
    sr_p.add_argument("--budget", type=float, default=0.5,
                       help="Max fraction of papers to label (default: 0.5)")

    # --- browse (C-2) ---
    br_p = subparsers.add_parser("browse", help="Fetch URL and extract paper metadata")
    br_p.add_argument("urls", nargs="+", help="One or more URLs to fetch")
    br_p.add_argument("--output", "-o", type=str, default=None,
                       help="Save results as JSON file")
    br_p.add_argument("--json", action="store_true", dest="json_output",
                       help="Print results as JSON")

    # --- skills (C-3) ---
    sk_p = subparsers.add_parser("skills", help="Manage and query skills")
    sk_p.add_argument("action", choices=["list", "match", "show", "context", "execute"],
                       help="list / match / show / context / execute")
    sk_p.add_argument("--query", "-q", type=str, default=None,
                       help="Query string for match/context")
    sk_p.add_argument("--name", "-n", type=str, default=None,
                       help="Skill name for show/execute")

    # --- mcp (C-1) ---
    mc_p = subparsers.add_parser("mcp", help="MCP Hub - manage servers and invoke tools")
    mc_p.add_argument("action", choices=["servers", "tools", "invoke", "status"],
                       help="servers / tools / invoke / status")
    mc_p.add_argument("--tool", "-t", type=str, default=None,
                       help="Tool name for invoke")
    mc_p.add_argument("--params", "-p", type=str, default=None,
                       help="JSON params for invoke")
    mc_p.add_argument("--params-file", "-f", type=str, default=None,
                       help="JSON file containing params for invoke")
    mc_p.add_argument("--config", type=str, default=None,
                       help="Path to MCP config JSON file")

    # --- orchestrate (C-4) ---
    or_p = subparsers.add_parser("orchestrate", help="Multi-Agent Orchestrator")
    or_p.add_argument("action", choices=["run", "agents", "decompose", "status"],
                       help="run / agents / decompose / status")
    or_p.add_argument("--goal", "-g", type=str, default=None,
                       help="Research goal for run/decompose")
    or_p.add_argument("--max", type=int, default=5, dest="max_results",
                       help="Max papers to retrieve (default: 5)")
    or_p.add_argument("--no-summary", action="store_true",
                       help="Skip LLM summary")

    # --- obsidian-export (T2-2) ---
    ob_p = subparsers.add_parser("obsidian-export", help="Export papers to Obsidian")
    ob_p.add_argument("input")

    # --- semantic-search (T3-1) ---
    ss_p = subparsers.add_parser("semantic-search", help="Semantic search in papers")
    ss_p.add_argument("query")
    ss_p.add_argument("--db", required=True)
    ss_p.add_argument("--top", type=int, default=10)

    # --- contradict (T3-2 + B-2) ---
    ct_p = subparsers.add_parser("contradict", help="Detect contradictions between papers")
    ct_p.add_argument("input")
    ct_p.add_argument("--use-llm", action="store_true",
                       help="Use Gemini LLM for semantic contradiction detection")

    # --- zotero-sync (T3-3) ---
    zt_p = subparsers.add_parser("zotero-sync", help="Sync papers to Zotero")
    zt_p.add_argument("input")

    # --- pipeline ---
    pl_p = subparsers.add_parser("pipeline", help="Run full pipeline")
    pl_p.add_argument("query", help="Search query")
    pl_p.add_argument("--max", type=int, default=20, dest="max_results",
                       help="Max papers per source (default: 20)")
    pl_p.add_argument("--provider", default="gemini", choices=["gemini", "codex"])
    pl_p.add_argument("--no-summary", action="store_true",
                       help="Skip LLM summary generation")
    pl_p.add_argument("--obsidian", action="store_true",
                       help="Export results to Obsidian Vault")
    pl_p.add_argument("--zotero", action="store_true",
                       help="Sync results to Zotero library")
    pl_p.add_argument("--prisma", action="store_true",
                       help="Generate PRISMA 2020 flow diagram")
    pl_p.add_argument("--bibtex", action="store_true",
                       help="Export results as BibTeX file")

    args = parser.parse_args(argv)
    cmd = args.command

    if cmd is None:
        parser.print_help()
        return 0

    dispatch = {
        "run": _cmd_run,
        "search": _cmd_search,
        "merge": _cmd_merge,
        "note": _cmd_note,
        "citation": _cmd_citation,
        "citation-stance": _cmd_citation_stance,
        "prisma": _cmd_prisma,
        "evidence": _cmd_evidence,
        "score": _cmd_score,
        "screen": _cmd_screen,
        "browse": _cmd_browse,
        "skills": _cmd_skills,
        "mcp": _cmd_mcp,
        "orchestrate": _cmd_orchestrate,
        "obsidian-export": _cmd_obsidian_export,
        "semantic-search": _cmd_semantic_search,
        "contradict": _cmd_contradict,
        "zotero-sync": _cmd_zotero_sync,
        "pipeline": _cmd_pipeline,
    }

    handler = dispatch.get(cmd)
    if handler:
        return handler(args)

    parser.print_help()
    return 0


# ====== Command handlers ======

def _cmd_run(args):
    from jarvis_core.app import run_task
    task_dict = {"goal": args.goal, "category": args.category,
                 "inputs": {"query": args.goal}}
    try:
        result = run_task(task_dict)
        print(f"  Status : {result.status}")
        print(f"  Log dir: {result.log_dir}")
        if result.answer:
            print(result.answer)
        return 0 if result.status == "success" else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def _cmd_search(args):
    from jarvis_cli.search import run_search
    return run_search(args)

def _cmd_merge(args):
    from jarvis_cli.merge import run_merge
    return run_merge(args)

def _cmd_note(args):
    from jarvis_cli.note import run_note
    result = run_note(args)
    if getattr(args, "obsidian", False) and result == 0:
        _do_obsidian_export(args.input)
    return result

def _cmd_citation(args):
    from jarvis_cli.citation import run_citation
    return run_citation(args)

def _cmd_citation_stance(args):
    from jarvis_cli.citation_stance import run_citation_stance
    args.use_llm = not getattr(args, "no_llm", False)
    return run_citation_stance(args)

def _cmd_prisma(args):
    from jarvis_cli.prisma import run_prisma
    return run_prisma(args)

def _cmd_evidence(args):
    from jarvis_cli.evidence import run_evidence
    return run_evidence(args)

def _cmd_score(args):
    from jarvis_cli.score import run_score
    return run_score(args)

def _cmd_screen(args):
    from jarvis_cli.screen import run_screen
    return run_screen(args)

def _cmd_browse(args):
    from jarvis_cli.browse import run_browse
    return run_browse(args)

def _cmd_skills(args):
    from jarvis_cli.skills import run_skills
    return run_skills(args)

def _cmd_mcp(args):
    from jarvis_cli.mcp import run_mcp
    return run_mcp(args)

def _cmd_orchestrate(args):
    from jarvis_cli.orchestrate import run_orchestrate
    return run_orchestrate(args)

def _cmd_obsidian_export(args):
    _do_obsidian_export(args.input)
    return 0

def _cmd_semantic_search(args):
    from jarvis_cli.semantic_search import run_semantic_search
    return run_semantic_search(args)

def _cmd_contradict(args):
    from jarvis_cli.contradict import run_contradict
    return run_contradict(args)

def _cmd_zotero_sync(args):
    from jarvis_cli.zotero_sync import run_zotero_sync
    return run_zotero_sync(args)

def _cmd_pipeline(args):
    from jarvis_cli.pipeline import run_pipeline
    return run_pipeline(args)

def _do_obsidian_export(input_path_str: str):
    """Shared Obsidian export logic."""
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
        print("  Error: JSON root must be an array.")
        return
    try:
        saved = export_papers_to_obsidian(papers)
        print(f"  Exported {len(saved)} papers to Obsidian Vault:")
        for p in saved[:5]:
            print(f"    - {p.name}")
    except Exception as e:
        print(f"  Error during Obsidian export: {e}")


if __name__ == "__main__":
    sys.exit(main())
