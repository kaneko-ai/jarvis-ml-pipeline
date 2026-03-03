"""jarvis orchestrate - LangGraph-based Multi-Agent Orchestrator.

Replaces v1.0 linear pipeline with a graph-based workflow:
- Conditional branching: if evidence is unknown → extra search loop
- Parallel-ready: SearchAgent results feed multiple downstream agents
- State management via TypedDict
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict
from jarvis_core.storage_utils import get_logs_dir

# ---------------------------------------------------------------------------
# Agent definitions (metadata only — no import of jarvis_core.agents)
# ---------------------------------------------------------------------------
AGENTS = [
    {"name": "SearchAgent",    "role": "search",    "desc": "Search papers via UnifiedSourceClient (PubMed, arXiv, Crossref, OpenAlex, S2)"},
    {"name": "EvidenceAgent",  "role": "analyze",   "desc": "Grade evidence levels using CEBM criteria (rule-based + optional LLM)"},
    {"name": "ScoringAgent",   "role": "score",     "desc": "Calculate paper quality scores (evidence + citations + recency)"},
    {"name": "SummarizeAgent", "role": "summarize", "desc": "Rank and summarize top papers"},
    {"name": "ReviewAgent",    "role": "review",    "desc": "Quality check: abstract coverage, DOI presence, duplicates"},
    {"name": "ChromaAgent",    "role": "store",     "desc": "Index papers into ChromaDB for persistent semantic search"},
]


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------
class OrchestratorState(TypedDict, total=False):
    goal: str
    max_results: int
    no_summary: bool
    papers: list[dict[str, Any]]
    graded_count: int
    scored_count: int
    unknown_evidence_count: int
    search_rounds: int
    review: dict[str, Any]
    chroma_indexed: int
    errors: list[str]
    elapsed: float


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------
def search_node(state: OrchestratorState) -> dict:
    """Search papers using UnifiedSourceClient."""
    goal = state["goal"]
    max_results = state.get("max_results", 5)
    search_rounds = state.get("search_rounds", 0)
    existing = state.get("papers", [])
    errors = list(state.get("errors", []))

    print(f"[SearchAgent] Searching papers (round {search_rounds + 1})...")

    try:
        from jarvis_core.sources.unified_source_client import (
            SourceType,
            UnifiedSourceClient,
        )

        client = UnifiedSourceClient()
        sources = [SourceType.PUBMED, SourceType.OPENALEX]
        unified = client.search(
            query=goal, max_results=max_results, sources=sources, deduplicate=True
        )

        new_papers = [up.to_dict() for up in unified]

        # Merge with existing, deduplicate by DOI
        existing_dois = {p.get("doi") for p in existing if p.get("doi")}
        for p in new_papers:
            doi = p.get("doi")
            if doi and doi in existing_dois:
                continue
            existing.append(p)
            if doi:
                existing_dois.add(doi)

        print(f"       Found {len(new_papers)} new, total {len(existing)} papers")
        return {"papers": existing, "search_rounds": search_rounds + 1}

    except Exception as e:
        print(f"       Error: {e}")
        errors.append(f"SearchAgent: {e}")
        return {"papers": existing, "search_rounds": search_rounds + 1, "errors": errors}


def evidence_node(state: OrchestratorState) -> dict:
    """Grade evidence levels for all papers."""
    papers = state.get("papers", [])
    errors = list(state.get("errors", []))

    print("[EvidenceAgent] Grading evidence levels...")
    graded = 0
    unknown_count = 0

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
                if grade.level.value == "unknown" or grade.confidence < 0.3:
                    unknown_count += 1
            else:
                p["evidence_level"] = "unknown"
                p["evidence_confidence"] = 0.0
                p["study_type"] = "unknown"
                unknown_count += 1

        print(f"       Graded {graded}/{len(papers)} (unknown/low: {unknown_count})")

    except Exception as e:
        print(f"       Error: {e}")
        errors.append(f"EvidenceAgent: {e}")

    return {
        "papers": papers,
        "graded_count": graded,
        "unknown_evidence_count": unknown_count,
        "errors": errors,
    }


def scoring_node(state: OrchestratorState) -> dict:
    """Calculate quality scores."""
    papers = state.get("papers", [])
    errors = list(state.get("errors", []))

    print("[ScoringAgent] Calculating quality scores...")

    try:
        from jarvis_cli.score import score_papers

        papers = score_papers(papers)
        scored = sum(1 for p in papers if "quality_score" in p)
        print(f"       Scored {scored}/{len(papers)} papers")
        return {"papers": papers, "scored_count": scored}

    except Exception as e:
        print(f"       Error: {e}")
        errors.append(f"ScoringAgent: {e}")
        return {"papers": papers, "scored_count": 0, "errors": errors}


def summarize_node(state: OrchestratorState) -> dict:
    """Rank and display top papers."""
    papers = state.get("papers", [])
    no_summary = state.get("no_summary", False)

    print("[SummarizeAgent] Ranking papers...")

    papers.sort(key=lambda p: p.get("quality_score", 0), reverse=True)
    top_n = min(5, len(papers))
    top_papers = papers[:top_n]

    if not no_summary:
        print(f"       Top {top_n} papers by quality score:")
        for i, p in enumerate(top_papers, 1):
            title = p.get("title", "Untitled")[:60]
            score = p.get("quality_score", 0)
            grade = p.get("quality_grade", "?")
            ev = p.get("evidence_level", "?")
            src = p.get("source", "?")
            print(f"       {i}. [{grade}] {score:.3f} | Ev:{ev} | {src} | {title}")

    return {"papers": papers}


def review_node(state: OrchestratorState) -> dict:
    """Quality checks on the final paper set."""
    papers = state.get("papers", [])

    print("[ReviewAgent] Quality checks...")

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

    review = {
        "total": n_total,
        "with_abstract": n_abstract,
        "with_doi": n_doi,
        "duplicate_dois": n_dup_doi,
    }
    return {"review": review}


def chroma_node(state: OrchestratorState) -> dict:
    """Index papers into ChromaDB for persistence."""
    papers = state.get("papers", [])
    errors = list(state.get("errors", []))

    print("[ChromaAgent] Indexing into ChromaDB...")

    try:
        from jarvis_core.embeddings.paper_store import PaperStore

        store = PaperStore()
        count = store.add_papers(papers)
        total = store.count()
        print(f"       Indexed {count} papers (ChromaDB total: {total})")
        return {"chroma_indexed": count}

    except Exception as e:
        print(f"       Error: {e}")
        errors.append(f"ChromaAgent: {e}")
        return {"chroma_indexed": 0, "errors": errors}


# ---------------------------------------------------------------------------
# Conditional edge: should we do another search round?
# ---------------------------------------------------------------------------
def should_retry_search(state: OrchestratorState) -> str:
    """If >50% papers have unknown evidence and we haven't retried, loop back."""
    papers = state.get("papers", [])
    unknown = state.get("unknown_evidence_count", 0)
    rounds = state.get("search_rounds", 0)

    if rounds < 2 and len(papers) > 0 and unknown / len(papers) > 0.5:
        print("       [Decision] High unknown rate — retrying search with refined query")
        return "retry_search"
    return "continue"


# ---------------------------------------------------------------------------
# Build the LangGraph
# ---------------------------------------------------------------------------
def _build_graph():
    """Construct the orchestration graph."""
    from langgraph.graph import END, StateGraph

    graph = StateGraph(OrchestratorState)

    # Add nodes
    graph.add_node("search", search_node)
    graph.add_node("evidence", evidence_node)
    graph.add_node("scoring", scoring_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("review", review_node)
    graph.add_node("chroma", chroma_node)

    # Set entry point
    graph.set_entry_point("search")

    # Edges
    graph.add_edge("search", "evidence")

    # Conditional: after evidence, decide retry or continue
    graph.add_conditional_edges(
        "evidence",
        should_retry_search,
        {
            "retry_search": "search",
            "continue": "scoring",
        },
    )

    graph.add_edge("scoring", "summarize")
    graph.add_edge("summarize", "review")
    graph.add_edge("review", "chroma")
    graph.add_edge("chroma", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# CLI handlers (same interface as before)
# ---------------------------------------------------------------------------
def _list_agents():
    """List all registered agents."""
    print()
    print("  JARVIS Multi-Agent Orchestrator (LangGraph)")
    print("  " + "=" * 50)
    print()
    for a in AGENTS:
        print(f"  [{a['name']}]  role={a['role']}")
        print(f"    {a['desc']}")
        print()
    print(f"  Total: {len(AGENTS)} agents")
    print(f"  Engine: LangGraph StateGraph")


def _decompose(args):
    """Decompose a goal into subtasks."""
    goal = getattr(args, "goal", None)
    if not goal:
        print("Error: --goal is required for decompose.", file=sys.stderr)
        return 1

    tasks = [
        {"step": 1, "agent": "SearchAgent",   "action": f"Search papers for: {goal}"},
        {"step": 2, "agent": "EvidenceAgent",  "action": "Grade evidence levels (CEBM)"},
        {"step": "2b", "agent": "SearchAgent", "action": "[Conditional] Re-search if >50% unknown evidence"},
        {"step": 3, "agent": "ScoringAgent",   "action": "Score paper quality"},
        {"step": 4, "agent": "SummarizeAgent", "action": "Rank and summarize top papers"},
        {"step": 5, "agent": "ReviewAgent",    "action": "Quality review and report"},
        {"step": 6, "agent": "ChromaAgent",    "action": "Index results into ChromaDB"},
    ]

    print()
    print(f"  Goal: {goal}")
    print(f"  Decomposed into {len(tasks)} tasks (LangGraph):")
    print()
    for t in tasks:
        print(f"  Step {t['step']}: [{t['agent']}] {t['action']}")
    print()
    return 0


def _show_status():
    """Show orchestrator status."""
    try:
        import langgraph
        lg_version = getattr(langgraph, "__version__", "installed")
    except ImportError:
        lg_version = "NOT INSTALLED"

    chroma_count = 0
    try:
        from jarvis_core.embeddings.paper_store import PaperStore
        chroma_count = PaperStore().count()
    except Exception:
        pass

    print()
    print("  Orchestrator Status (LangGraph)")
    print("  " + "-" * 40)
    print(f"  Agents registered : {len(AGENTS)}")
    print(f"  LangGraph version : {lg_version}")
    print(f"  Pipeline engine   : StateGraph")
    print(f"  Conditional edges : evidence → retry_search / continue")
    print(f"  ChromaDB papers   : {chroma_count}")
    print(f"  Available sources : PubMed, arXiv, Crossref, OpenAlex, Semantic Scholar")
    print()


def _run_pipeline(args):
    """Run the full LangGraph orchestration pipeline."""
    goal = getattr(args, "goal", None)
    if not goal:
        print("Error: --goal is required for run.", file=sys.stderr)
        return 1

    max_results = getattr(args, "max", 5)
    no_summary = getattr(args, "no_summary", False)

    print()
    print("=" * 60)
    print(f"  JARVIS Orchestration Pipeline (LangGraph)")
    print(f"  Goal: {goal}")
    print(f"  Max papers per source: {max_results}")
    print("=" * 60)
    print()

    pipeline_start = time.perf_counter()

    try:
        workflow = _build_graph()
    except ImportError as e:
        print(f"  Error: LangGraph not installed ({e})")
        print(f"  Install with: python -m pip install langgraph")
        return 1

    # Run the graph
    initial_state: OrchestratorState = {
        "goal": goal,
        "max_results": max_results,
        "no_summary": no_summary,
        "papers": [],
        "graded_count": 0,
        "scored_count": 0,
        "unknown_evidence_count": 0,
        "search_rounds": 0,
        "review": {},
        "chroma_indexed": 0,
        "errors": [],
        "elapsed": 0.0,
    }

    try:
        final_state = workflow.invoke(initial_state)
    except Exception as e:
        print(f"  Pipeline error: {e}")
        return 1

    elapsed = time.perf_counter() - pipeline_start
    papers = final_state.get("papers", [])
    review = final_state.get("review", {})
    errors = final_state.get("errors", [])

    # Save results
    results = {
        "goal": goal,
        "timestamp": datetime.now().isoformat(),
        "engine": "langgraph",
        "search_rounds": final_state.get("search_rounds", 0),
        "papers_count": len(papers),
        "graded_count": final_state.get("graded_count", 0),
        "scored_count": final_state.get("scored_count", 0),
        "chroma_indexed": final_state.get("chroma_indexed", 0),
        "review": review,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 2),
        "papers": papers,
    }

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in goal)[:40]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = get_logs_dir("orchestrate")
    # mkdir handled by get_logs_dir
    out_path = log_dir / f"{safe_name}_{ts}.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=" * 60)
    print(f"  Orchestration completed in {elapsed:.1f}s")
    print(f"  Engine: LangGraph StateGraph")
    print(f"  Search rounds: {final_state.get('search_rounds', 0)}")
    print(f"  {len(papers)} papers processed by {len(AGENTS)} agents")
    print(f"  ChromaDB indexed: {final_state.get('chroma_indexed', 0)}")
    if errors:
        print(f"  Warnings: {len(errors)}")
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
