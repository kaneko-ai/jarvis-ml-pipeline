"""jarvis deep-research - Autonomous deep research mode.

Implements GPT-Researcher-style workflow using multiple LLM backends:
  Fallback chain: Codex CLI → Copilot CLI → Gemini API (via LiteLLM)

Phases:
1. Query decomposition (LLM splits goal into sub-queries)
2. Multi-source search (PubMed, OpenAlex, Semantic Scholar)
3. Evidence grading + scoring
4. ChromaDB indexing
5. LLM-based synthesis report generation

No OpenAI API key required.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

PROJECT_DIR = Path(r"C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline")
_last_llm_call = 0.0
_LLM_CALL_INTERVAL = 3.0


# ---------------------------------------------------------------------------
# LLM backends: Codex CLI → Copilot CLI → Gemini API
# ---------------------------------------------------------------------------
def _call_codex(prompt: str, timeout: int = 120) -> Optional[str]:
    """Call Codex CLI via stdin pipe."""
    try:
        result = subprocess.run(
            ["codex", "exec", "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_DIR),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return None


def _call_copilot(prompt: str, timeout: int = 120) -> Optional[str]:
    """Call GitHub Copilot CLI."""
    try:
        result = subprocess.run(
            ["copilot", "-p", prompt[:3000]],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_DIR),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return None


def _call_gemini(prompt: str, system: str = "You are a research assistant.",
                 temperature: float = 0.3, max_tokens: int = 3000) -> Optional[str]:
    """Call Gemini via LiteLLM with retry on rate limit."""
    try:
        from jarvis_core.llm.litellm_client import completion
        for attempt in range(3):
            try:
                return completion(prompt, system=system,
                                 temperature=temperature, max_tokens=max_tokens)
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    wait = 30 * (attempt + 1)
                    print(f"  [Gemini] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
    except Exception:
        pass
    return None


def _llm_complete(prompt: str, system: str = "You are a research assistant.",
                  temperature: float = 0.3, max_tokens: int = 3000) -> str:
    """Fallback chain: Codex CLI → Copilot CLI → Gemini API."""
    global _last_llm_call

    # Rate limit
    elapsed = time.time() - _last_llm_call
    if elapsed < _LLM_CALL_INTERVAL:
        time.sleep(_LLM_CALL_INTERVAL - elapsed)

    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    # 1. Codex CLI
    print("  [LLM] Trying Codex CLI...", end=" ")
    result = _call_codex(full_prompt)
    if result:
        print("OK")
        _last_llm_call = time.time()
        return result
    print("skip")

    # 2. Copilot CLI
    print("  [LLM] Trying Copilot CLI...", end=" ")
    result = _call_copilot(full_prompt[:3000])
    if result:
        print("OK")
        _last_llm_call = time.time()
        return result
    print("skip")

    # 3. Gemini API
    print("  [LLM] Trying Gemini API...", end=" ")
    result = _call_gemini(prompt, system=system,
                          temperature=temperature, max_tokens=max_tokens)
    if result:
        print("OK")
        _last_llm_call = time.time()
        return result
    print("FAIL")

    return "(LLM unavailable - all providers failed)"


# ---------------------------------------------------------------------------
# Deep Research phases
# ---------------------------------------------------------------------------
def _decompose_query(goal: str, max_sub: int = 3) -> list[str]:
    """Use LLM to decompose a research goal into sub-queries."""
    prompt = (
        f"You are a research assistant. Decompose this research goal "
        f"into {max_sub} specific search queries for academic databases "
        f"(PubMed, OpenAlex). Return ONLY a JSON array of strings, "
        f"no explanation.\n\n"
        f"Research goal: {goal}\n\n"
        f'Example output: ["query1", "query2", "query3"]'
    )

    result = _llm_complete(prompt, temperature=0.2, max_tokens=500)

    try:
        match = re.search(r'\[.*?\]', result, re.DOTALL)
        if match:
            queries = json.loads(match.group())
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                return queries[:max_sub]
    except (json.JSONDecodeError, Exception):
        pass

    # Fallback: return original goal
    return [goal]


def _search_papers(queries: list[str], max_per_query: int = 5) -> list[dict]:
    """Search across multiple queries and deduplicate."""
    all_papers = []
    seen_dois = set()

    try:
        from jarvis_core.sources.unified_source_client import (
            SourceType,
            UnifiedSourceClient,
        )

        client = UnifiedSourceClient()
        sources = [SourceType.PUBMED, SourceType.OPENALEX]

        for i, query in enumerate(queries, 1):
            print(f"  [Search {i}/{len(queries)}] {query}")
            try:
                unified = client.search(
                    query=query,
                    max_results=max_per_query,
                    sources=sources,
                    deduplicate=True,
                )
                count = 0
                for up in unified:
                    p = up.to_dict()
                    doi = p.get("doi")
                    if doi and doi in seen_dois:
                        continue
                    all_papers.append(p)
                    if doi:
                        seen_dois.add(doi)
                    count += 1
                print(f"           Found {count} new papers")
                time.sleep(1)  # Rate limit courtesy
            except Exception as e:
                print(f"           Error: {e}")

    except ImportError as e:
        print(f"  [Search] Import error: {e}")

    return all_papers


def _grade_and_score(papers: list[dict]) -> list[dict]:
    """Grade evidence and calculate scores."""
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
            else:
                p["evidence_level"] = "unknown"
                p["evidence_confidence"] = 0.0
                p["study_type"] = "unknown"
    except Exception as e:
        print(f"  [Evidence] Error: {e}")

    try:
        from jarvis_cli.score import score_papers
        papers = score_papers(papers)
    except Exception as e:
        print(f"  [Scoring] Error: {e}")

    return papers


def _index_to_chroma(papers: list[dict]) -> int:
    """Index papers into ChromaDB."""
    try:
        from jarvis_core.embeddings.paper_store import PaperStore

        store = PaperStore()
        count = store.add_papers(papers)
        return count
    except Exception as e:
        print(f"  [ChromaDB] Error: {e}")
        return 0


def _generate_report(goal: str, papers: list[dict], max_papers: int = 10) -> str:
    """Generate a synthesis report using LLM fallback chain."""
    top_papers = sorted(
        papers, key=lambda p: p.get("quality_score", 0), reverse=True
    )[:max_papers]

    paper_summaries = []
    for i, p in enumerate(top_papers, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "?")
        evidence = p.get("evidence_level", "?")
        abstract = p.get("abstract", "")[:300]
        doi = p.get("doi", "")
        paper_summaries.append(
            f"{i}. {title} ({year}) [Evidence: {evidence}] DOI: {doi}\n   {abstract}"
        )

    papers_text = "\n\n".join(paper_summaries)

    prompt = (
        f"You are a research synthesis expert. Based on the following papers, "
        f"write a comprehensive research report on: {goal}\n\n"
        f"Papers found:\n{papers_text}\n\n"
        f"Write the report in Markdown format with these sections:\n"
        f"# Research Report: {goal}\n"
        f"## Overview\n"
        f"## Key Findings\n"
        f"## Evidence Summary\n"
        f"## Gaps and Future Directions\n"
        f"## References\n\n"
        f"Be concise but thorough. Cite papers by number."
    )

    report = _llm_complete(prompt, temperature=0.3, max_tokens=3000)

    if "(LLM unavailable" in report:
        # Fallback: basic text report
        lines = [
            f"# Research Report: {goal}",
            "",
            f"## Papers Found: {len(papers)}",
            "",
        ]
        for i, p in enumerate(top_papers, 1):
            title = p.get("title", "Untitled")
            score = p.get("quality_score", 0)
            ev = p.get("evidence_level", "?")
            lines.append(f"{i}. [{ev}] (score={score:.3f}) {title}")
        return "\n".join(lines)

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def run_deep_research(args) -> int:
    """CLI entry point for deep-research command."""
    goal = args.goal
    max_sources = getattr(args, "max_sources", 20)
    output = getattr(args, "output", None)
    no_report = getattr(args, "no_report", False)

    max_per_query = max(3, max_sources // 3)

    print()
    print("=" * 60)
    print("  JARVIS Deep Research")
    print(f"  Goal: {goal}")
    print(f"  Max sources: {max_sources}")
    print(f"  LLM chain: Codex CLI → Copilot CLI → Gemini API")
    print("=" * 60)
    print()

    total_start = time.perf_counter()

    # Phase 1: Decompose
    print("[Phase 1] Decomposing research goal...")
    sub_queries = _decompose_query(goal, max_sub=3)
    print(f"  Sub-queries ({len(sub_queries)}):")
    for i, q in enumerate(sub_queries, 1):
        print(f"    {i}. {q}")
    print()

    # Phase 2: Search
    print("[Phase 2] Multi-source search...")
    papers = _search_papers(sub_queries, max_per_query=max_per_query)
    print(f"  Total papers collected: {len(papers)}")
    print()

    if not papers:
        print("  No papers found. Deep research stopped.")
        return 1

    # Phase 3: Grade & Score
    print("[Phase 3] Evidence grading + quality scoring...")
    papers = _grade_and_score(papers)
    scored = sum(1 for p in papers if "quality_score" in p)
    print(f"  Graded and scored: {scored}/{len(papers)}")
    print()

    # Phase 4: ChromaDB Index
    print("[Phase 4] Indexing to ChromaDB...")
    indexed = _index_to_chroma(papers)
    print(f"  Indexed {indexed} papers")
    print()

    # Phase 5: Report
    report = ""
    if not no_report:
        print("[Phase 5] Generating synthesis report...")
        report = _generate_report(goal, papers)
        print(f"  Report generated ({len(report)} chars)")
        print()

    # Save output
    elapsed = time.perf_counter() - total_start

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in goal)[:40]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_dir = Path("logs") / "deep_research"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON results
    results = {
        "goal": goal,
        "timestamp": datetime.now().isoformat(),
        "llm_chain": "codex_cli -> copilot_cli -> gemini_api",
        "sub_queries": sub_queries,
        "papers_count": len(papers),
        "indexed_count": indexed,
        "elapsed_seconds": round(elapsed, 2),
        "papers": papers,
    }
    json_path = log_dir / f"{safe_name}_{ts}.json"
    json_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Save report
    report_path = None
    if report:
        if output:
            report_path = Path(output)
        else:
            report_path = log_dir / f"{safe_name}_{ts}_report.md"
        report_path.write_text(report, encoding="utf-8")

    print("=" * 60)
    print(f"  Deep Research completed in {elapsed:.1f}s")
    print(f"  LLM chain: Codex CLI → Copilot CLI → Gemini API")
    print(f"  Papers: {len(papers)} found, {indexed} indexed")
    print(f"  Sub-queries used: {len(sub_queries)}")
    print(f"  JSON: {json_path}")
    if report_path:
        print(f"  Report: {report_path}")
    print("=" * 60)
    return 0
