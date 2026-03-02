"""jarvis orchestrate - Multi-Agent Orchestrator (C-4).

Uses existing JARVIS modules directly instead of orchestrator.py
to avoid the agents.py / agents/ package conflict.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Agent definitions (lightweight, no import of jarvis_core.agents.orchestrator)
# ---------------------------------------------------------------------------
AGENTS = [
    {"name": "SearchAgent",    "role": "search",    "desc": "Search papers via UnifiedSourceClient (PubMed, arXiv, Crossref, OpenAlex, S2)"},
    {"name": "EvidenceAgent",  "role": "analyze",   "desc": "Grade evidence levels using CEBM criteria (rule-based + optional LLM)"},
    {"name": "ScoringAgent",   "role": "score",     "desc": "Calculate paper quality scores (evidence + citations + recency)"},
    {"name": "SummarizeAgent", "role": "summarize", "desc": "Rank and summarize top papers"},
    {"name": "ReviewAgent",    "role": "review",    "desc": "Quality check: abstract coverage, DOI presence, duplicates"},
]


def _list_agents():
    """List all registered agents."""
    print()
    print("  JARVIS Multi-Agent Orchestrator")
    print("  " + "=" * 50)
    print()
    for a in AGENTS:
        print(f"  [{a['name']}]  role={a['role']}")
        print(f"    {a['desc']}")
        print()
    print(f"  Total: {len(AGENTS)} agents")


def _decompose(args):
    """Decompose a goal into subtasks."""
    goal = getattr(args, "goal", None)
    if not goal:
        print("Error: --goal is required for decompose.", file=sys.stderr)
        return 1

    tasks = [
        {"step": 1, "agent": "SearchAgent",   "action": f"Search papers for: {goal}"},
        {"step": 2, "agent": "EvidenceAgent",  "action": "Grade evidence levels (CEBM)"},
        {"step": 3, "agent": "ScoringAgent",   "action": "Score paper quality"},
        {"step": 4, "agent": "SummarizeAgent", "action": "Rank and summarize top papers"},
        {"step": 5, "agent": "ReviewAgent",    "action": "Quality review and report"},
    ]

    print()
    print(f"  Goal: {goal}")
    print(f"  Decomposed into {len(tasks)} tasks:")
    print()
    for t in tasks:
        print(f"  Step {t['step']}: [{t['agent']}] {t['action']}")
    print()
    return 0


def _show_status():
    """Show orchestrator status."""
    print()
    print("  Orchestrator Status")
    print("  " + "-" * 40)
    print(f"  Agents registered : {len(AGENTS)}")
    print(f"  Pipeline ready    : Yes")
    print(f"  Available sources : PubMed, arXiv, Crossref, OpenAlex, Semantic Scholar")
    print()


def _run_pipeline(args):
    """Run the full orchestration pipeline."""
    goal = getattr(args, "goal", None)
    if not goal:
        print("Error: --goal is required for run.", file=sys.stderr)
        return 1

    max_results = getattr(args, "max", 5)
    no_summary = getattr(args, "no_summary", False)

    print()
    print("=" * 60)
    print(f"  JARVIS Orchestration Pipeline")
    print(f"  Goal: {goal}")
    print(f"  Max papers per source: {max_results}")
    print("=" * 60)
    print()

    pipeline_start = time.perf_counter()
    results = {"goal": goal, "timestamp": datetime.now().isoformat(), "agents": {}}
    papers = []

    # --- Step 1: Search Agent ---
    print("[1/5] SearchAgent: Searching papers...")
    try:
        from jarvis_core.sources.unified_source_client import (
            SourceType,
            UnifiedSourceClient,
        )

        client = UnifiedSourceClient()
        sources = [SourceType.PUBMED, SourceType.OPENALEX]
        unified = client.search(query=goal, max_results=max_results, sources=sources, deduplicate=True)

        for up in unified:
            papers.append(up.to_dict())

        print(f"       Found {len(papers)} papers (deduplicated)")
        results["agents"]["SearchAgent"] = {"status": "ok", "count": len(papers)}
    except Exception as e:
        print(f"       Error: {e}")
        results["agents"]["SearchAgent"] = {"status": "error", "error": str(e)}

    if not papers:
        print("\n  No papers found. Pipeline stopped.")
        return 1

    # --- Step 2: Evidence Agent ---
    print("[2/5] EvidenceAgent: Grading evidence levels...")
    graded = 0
    try:
        from jarvis_core.evidence import grade_evidence

        for p in papers:
            title = p.get("title", "")
            abstract = p.get("abstract", "")
            if title or abstract:
                grade = grade_evidence(title=title, abstract=abstract, use_llm=False)
                p["evidence_level"] = grade.level.value
                p["evidence_confidence"] = round(grade.confidence, 3)
                p["study_type"] = grade.study_type.value
                graded += 1
            else:
                p["evidence_level"] = "unknown"
                p["evidence_confidence"] = 0.0
                p["study_type"] = "unknown"

        print(f"       Graded {graded}/{len(papers)} papers")
        results["agents"]["EvidenceAgent"] = {"status": "ok", "graded": graded}
    except Exception as e:
        print(f"       Error: {e}")
        results["agents"]["EvidenceAgent"] = {"status": "error", "error": str(e)}

    # --- Step 3: Scoring Agent ---
    print("[3/5] ScoringAgent: Calculating quality scores...")
    try:
        from jarvis_cli.score import score_papers

        papers = score_papers(papers)
        scored = sum(1 for p in papers if "quality_score" in p)
        print(f"       Scored {scored}/{len(papers)} papers")
        results["agents"]["ScoringAgent"] = {"status": "ok", "scored": scored}
    except Exception as e:
        print(f"       Error: {e}")
        results["agents"]["ScoringAgent"] = {"status": "error", "error": str(e)}

    # --- Step 4: Summarize Agent ---
    print("[4/5] SummarizeAgent: Ranking papers...")
    papers.sort(key=lambda p: p.get("quality_score", 0), reverse=True)
    top_n = min(5, len(papers))
    top_papers = papers[:top_n]

    print(f"       Top {top_n} papers ranked by quality score:")
    for i, p in enumerate(top_papers, 1):
        title = p.get("title", "Untitled")[:60]
        score = p.get("quality_score", 0)
        grade = p.get("quality_grade", "?")
        ev = p.get("evidence_level", "?")
        src = p.get("source", "?")
        print(f"       {i}. [{grade}] {score:.3f} | Ev:{ev} | {src} | {title}")

    results["agents"]["SummarizeAgent"] = {"status": "ok", "top_n": top_n}

    # --- Step 5: Review Agent ---
    print("[5/5] ReviewAgent: Quality checks...")
    n_abstract = sum(1 for p in papers if p.get("abstract"))
    n_doi = sum(1 for p in papers if p.get("doi"))
    n_total = len(papers)

    dois = [p["doi"] for p in papers if p.get("doi")]
    n_dup_doi = len(dois) - len(set(dois))

    print(f"       Papers: {n_total}")
    print(f"       With abstract: {n_abstract}/{n_total}")
    print(f"       With DOI: {n_doi}/{n_total}")
    if n_dup_doi > 0:
        print(f"       WARNING: {n_dup_doi} duplicate DOIs detected")

    results["agents"]["ReviewAgent"] = {
        "status": "ok",
        "total": n_total,
        "with_abstract": n_abstract,
        "with_doi": n_doi,
        "duplicate_dois": n_dup_doi,
    }

    # --- Save results ---
    elapsed = time.perf_counter() - pipeline_start
    results["elapsed_seconds"] = round(elapsed, 2)
    results["papers"] = papers

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in goal)[:40]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs") / "orchestrate"
    log_dir.mkdir(parents=True, exist_ok=True)
    out_path = log_dir / f"{safe_name}_{ts}.json"

    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=" * 60)
    print(f"  Orchestration completed in {elapsed:.1f}s")
    print(f"  {n_total} papers processed by {len(AGENTS)} agents")
    print(f"  Results saved to: {out_path}")
    print("=" * 60)
    return 0


def run_orchestrate(args):
    """Dispatch orchestrate sub-commands."""
    action = getattr(args, "action", "run")

    if action == "agents":
        _list_agents()
        return 0
    elif action == "status":
        _show_status()
        return 0
    elif action == "decompose":
        return _decompose(args)
    elif action == "run":
        return _run_pipeline(args)
    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        return 1
