"""jarvis pipeline - End-to-end literature review pipeline (T4-1).

Runs: search -> dedup -> evidence grading -> Obsidian export -> Zotero sync
All in one command.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path


def run_pipeline(args) -> int:
    """Run the full JARVIS pipeline."""
    query = args.query
    max_results = min(args.max_results, 100)
    do_obsidian = getattr(args, "obsidian", False)
    do_zotero = getattr(args, "zotero", False)
    provider = getattr(args, "provider", "gemini")

    execution_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = time.time()

    print("=" * 60)
    print("  JARVIS Pipeline - End-to-end Literature Review")
    print("=" * 60)
    print(f"  Query      : {query}")
    print(f"  Max papers : {max_results}")
    print(f"  Obsidian   : {'Yes' if do_obsidian else 'No'}")
    print(f"  Zotero     : {'Yes' if do_zotero else 'No'}")
    print(f"  Execution  : {execution_id}")
    print("=" * 60)
    print()

    # ========================================
    # Step 1: Search papers from multiple sources
    # ========================================
    print("[Step 1/5] Searching papers...")
    papers = _step_search(query, max_results)
    if not papers:
        print("  No papers found. Pipeline stopped.")
        return 1
    print(f"  Found {len(papers)} papers.")
    print()

    # ========================================
    # Step 2: Deduplicate
    # ========================================
    print("[Step 2/5] Deduplicating...")
    before_count = len(papers)
    papers = _step_dedup(papers)
    after_count = len(papers)
    removed = before_count - after_count
    print(f"  {before_count} -> {after_count} papers ({removed} duplicates removed)")
    print()

    # ========================================
    # Step 3: Evidence grading
    # ========================================
    print("[Step 3/5] Grading evidence levels...")
    papers = _step_evidence(papers)
    level_counts = {}
    for p in papers:
        lv = p.get("evidence_level", "unknown")
        level_counts[lv] = level_counts.get(lv, 0) + 1
    print(f"  Evidence distribution: {level_counts}")
    print()

    # ========================================
    # Step 4: Save results
    # ========================================
    print("[Step 4/5] Saving results...")
    log_dir = Path("logs/pipeline")
    log_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)
    safe_name = safe_name.strip().replace(" ", "_")[:50]
    base_name = f"{safe_name}_{timestamp}"

    json_path = log_dir / f"{base_name}.json"
    json_path.write_text(
        json.dumps(papers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  JSON: {json_path}")

    # ========================================
    # Step 4b: Obsidian export (optional)
    # ========================================
    obsidian_count = 0
    if do_obsidian:
        print()
        print("  Exporting to Obsidian Vault...")
        obsidian_count = _step_obsidian(papers)
        print(f"  Exported {obsidian_count} papers to Obsidian.")

    # ========================================
    # Step 4c: Zotero sync (optional)
    # ========================================
    zotero_count = 0
    if do_zotero:
        print()
        print("  Syncing to Zotero...")
        zotero_count = _step_zotero(papers)
        print(f"  Synced {zotero_count} papers to Zotero.")

    # ========================================
    # Step 5: Save execution log
    # ========================================
    print()
    print("[Step 5/5] Saving execution log...")
    duration = time.time() - start_time

    exec_log = {
        "execution_id": execution_id,
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "sources": ["pubmed", "openalex"],
        "max_requested": max_results,
        "total_retrieved": before_count,
        "after_dedup": after_count,
        "evidence_grading": level_counts,
        "obsidian_export": obsidian_count,
        "zotero_sync": zotero_count,
        "output_file": str(json_path),
        "duration_seconds": round(duration, 1),
    }

    log_path = log_dir / f"{base_name}_log.json"
    log_path.write_text(
        json.dumps(exec_log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Log: {log_path}")

    print()
    print("=" * 60)
    print(f"  Pipeline completed in {duration:.1f}s")
    print(f"  Papers: {after_count} (from {before_count})")
    print(f"  Output: {json_path}")
    if do_obsidian:
        print(f"  Obsidian: {obsidian_count} exported")
    if do_zotero:
        print(f"  Zotero: {zotero_count} synced")
    print("=" * 60)

    return 0


def _step_search(query: str, max_results: int) -> list[dict]:
    """Search papers using UnifiedSourceClient or fallback."""
    try:
        from jarvis_core.sources import UnifiedSourceClient

        client = UnifiedSourceClient()
        from jarvis_core.sources.unified_source_client import SourceType

        sources = [SourceType.PUBMED, SourceType.OPENALEX]
        unified_papers = client.search(
            query, max_results=max_results, sources=sources
        )

        papers = []
        for up in unified_papers:
            papers.append({
                "title": up.title or "",
                "abstract": up.abstract or "",
                "authors": up.authors or [],
                "year": up.year,
                "journal": up.venue or "",
                "doi": up.doi or "",
                "pmid": up.pmid or "",
                "citation_count": up.citation_count or 0,
                "url": up.url or "",
                "source": up.source.value if up.source else "unknown",
                "keywords": up.keywords or [],
            })
        return papers

    except Exception as e:
        print(f"  Warning: UnifiedSourceClient failed ({e})")
        print("  Falling back to PubMed only...")

        try:
            from jarvis_core.sources import PubMedClient

            client = PubMedClient()
            articles = client.search_and_fetch(query, max_results=max_results)
            papers = []
            for a in articles:
                papers.append({
                    "title": a.title or "",
                    "abstract": a.abstract or "",
                    "authors": a.authors or [],
                    "year": a.pub_date[:4] if a.pub_date else "",
                    "journal": a.journal or "",
                    "doi": a.doi or "",
                    "pmid": a.pmid or "",
                    "source": "pubmed",
                })
            return papers
        except Exception as e2:
            print(f"  Error: PubMed also failed: {e2}")
            return []


def _step_dedup(papers: list[dict]) -> list[dict]:
    """Remove duplicate papers by DOI or title."""
    seen_doi = set()
    seen_title = set()
    unique = []

    for p in papers:
        doi = (p.get("doi") or "").strip().lower()
        title = (p.get("title") or "").strip().lower()

        if doi and doi in seen_doi:
            continue
        if title and title in seen_title:
            continue

        if doi:
            seen_doi.add(doi)
        if title:
            seen_title.add(title)
        unique.append(p)

    return unique


def _step_evidence(papers: list[dict]) -> list[dict]:
    """Grade evidence level for each paper."""
    try:
        from jarvis_core.evidence import grade_evidence
    except ImportError:
        print("  Warning: evidence module not available, skipping.")
        return papers

    for p in papers:
        title = p.get('title', '')
        abstract = p.get('abstract', '')

        grade = grade_evidence(title=title, abstract=abstract, use_llm=False)

        level_val = grade.level.value if grade.level else "unknown"
        study_val = grade.study_type.value if grade.study_type else "unknown"
        conf = grade.confidence

        # If rule-based returns unknown, try simple keyword fallback
        if level_val == "unknown":
            level_val, study_val, conf = _fallback_classify(title, abstract)

        p["evidence_level"] = level_val
        p["evidence_confidence"] = conf
        p["study_type"] = study_val

    return papers


def _fallback_classify(title: str, abstract: str) -> tuple:
    """Simple keyword-based fallback when rule-based classifier returns unknown."""
    text = (title + " " + abstract).lower()

    # Check keywords in order of evidence strength
    patterns = [
        (["systematic review", "meta-analysis", "meta analysis"], "1a", "systematic_review", 0.6),
        (["randomized", "randomised", "rct", "double-blind", "placebo-controlled"], "1b", "randomized_controlled_trial", 0.6),
        (["prospective cohort", "longitudinal study"], "2b", "prospective_cohort", 0.5),
        (["cohort study", "cohort analysis"], "2b", "cohort_study", 0.5),
        (["case-control", "case control"], "3b", "case_control", 0.5),
        (["cross-sectional", "cross sectional", "survey study"], "3b", "cross_sectional", 0.4),
        (["case report", "case series", "case study"], "4", "case_report", 0.4),
        (["in vitro", "in vivo", "cell line", "mouse model", "animal model", "mice"], "5", "experimental_basic", 0.5),
        (["review", "overview", "summarize", "summarise"], "5", "narrative_review", 0.3),
    ]

    for keywords, level, study_type, confidence in patterns:
        for kw in keywords:
            if kw in text:
                return (level, study_type, confidence)

    return ("5", "unknown", 0.1)


def _step_obsidian(papers: list[dict]) -> int:
    """Export papers to Obsidian Vault."""
    try:
        from jarvis_cli.obsidian_export import export_papers_to_obsidian
        saved = export_papers_to_obsidian(papers)
        return len(saved)
    except Exception as e:
        print(f"  Warning: Obsidian export failed: {e}")
        return 0


def _step_zotero(papers: list[dict]) -> int:
    """Sync papers to Zotero."""
    try:
        from jarvis_cli.zotero_sync import _get_zotero_client, _build_zotero_item
        from jarvis_cli.zotero_sync import _get_crossref_metadata, _get_doi_from_crossref
        import time as _time

        zot = _get_zotero_client()
        if zot is None:
            return 0

        count = 0
        for p in papers:
            doi = p.get("doi") or p.get("DOI")
            if not doi:
                doi = _get_doi_from_crossref(p.get("title", ""))
            if not doi:
                continue

            try:
                meta = _get_crossref_metadata(doi)
                item = _build_zotero_item(zot, doi, meta)
                zot.create_items([item])
                count += 1
            except Exception:
                pass

            _time.sleep(1)

        return count

    except Exception as e:
        print(f"  Warning: Zotero sync failed: {e}")
        return 0
