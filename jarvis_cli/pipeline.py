"""jarvis pipeline - End-to-end literature review pipeline.

Runs: search -> dedup (fuzzy) -> evidence grading -> scoring -> LLM summary
      -> save -> [Obsidian] -> [Zotero] -> [PRISMA] -> [BibTeX] -> log
"""

from __future__ import annotations

import json
import re
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
    do_summary = not getattr(args, "no_summary", False)
    do_prisma = getattr(args, "prisma", False)
    do_bibtex = getattr(args, "bibtex", False)
    provider = getattr(args, "provider", "gemini")

    execution_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = time.time()

    print("=" * 60)
    print("  JARVIS Pipeline - End-to-end Literature Review")
    print("=" * 60)
    print(f"  Query      : {query}")
    print(f"  Max papers : {max_results}")
    print(f"  LLM Summary: {'Yes (' + provider + ')' if do_summary else 'No'}")
    print(f"  Obsidian   : {'Yes' if do_obsidian else 'No'}")
    print(f"  Zotero     : {'Yes' if do_zotero else 'No'}")
    print(f"  PRISMA     : {'Yes' if do_prisma else 'No'}")
    print(f"  BibTeX     : {'Yes' if do_bibtex else 'No'}")
    print(f"  Execution  : {execution_id}")
    print("=" * 60)
    print()

    # Step 1: Search
    print("[Step 1/7] Searching papers...")
    papers = _step_search(query, max_results)
    if not papers:
        print("  No papers found. Pipeline stopped.")
        return 1
    print(f"  Found {len(papers)} papers.")
    print()

    # Step 2: Dedup
    print("[Step 2/7] Deduplicating (DOI + exact title + fuzzy title)...")
    before_count = len(papers)
    papers = _step_dedup(papers)
    after_count = len(papers)
    removed = before_count - after_count
    print(f"  {before_count} -> {after_count} papers ({removed} duplicates removed)")
    print()

    # Step 3: Evidence grading
    print("[Step 3/7] Grading evidence levels...")
    papers = _step_evidence(papers)
    level_counts = {}
    for p in papers:
        lv = p.get("evidence_level", "unknown")
        level_counts[lv] = level_counts.get(lv, 0) + 1
    print(f"  Evidence distribution: {level_counts}")
    print()

    # Step 4: Paper scoring (B-3)
    print("[Step 4/7] Scoring paper quality...")
    papers = _step_scoring(papers)
    grades = {}
    for p in papers:
        g = p.get("quality_grade", "?")
        grades[g] = grades.get(g, 0) + 1
    print(f"  Grade distribution: {grades}")
    print()

    # Step 5: LLM Summary (A-1)
    summary_count = 0
    if do_summary:
        print(f"[Step 5/7] Generating Japanese summaries via {provider}...")
        papers, summary_count = _step_summarize(papers, provider)
        print(f"  Summarized {summary_count}/{len(papers)} papers.")
    else:
        print("[Step 5/7] LLM Summary: skipped (--no-summary)")
    print()

    # Step 6: Save results + optional exports
    print("[Step 6/7] Saving results...")
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

    # --- Obsidian export ---
    obsidian_count = 0
    if do_obsidian:
        print()
        print("  Exporting to Obsidian Vault...")
        obsidian_count = _step_obsidian(papers)
        print(f"  Exported {obsidian_count} papers to Obsidian.")

    # --- Zotero sync ---
    zotero_count = 0
    if do_zotero:
        print()
        print("  Syncing to Zotero...")
        zotero_count = _step_zotero(papers)
        print(f"  Synced {zotero_count} papers to Zotero.")

    # --- PRISMA diagram (A-4) ---
    prisma_path = ""
    if do_prisma:
        print()
        print("  Generating PRISMA 2020 flow diagram...")
        prisma_path = _step_prisma(str(json_path), log_dir, base_name)
        if prisma_path:
            print(f"  PRISMA: {prisma_path}")

    # --- BibTeX export (A-5) ---
    bibtex_path = ""
    if do_bibtex:
        print()
        print("  Generating BibTeX file...")
        bibtex_path = _step_bibtex(papers, log_dir, base_name)
        if bibtex_path:
            print(f"  BibTeX: {bibtex_path}")

    # Step 7: Save execution log
    print()
    print("[Step 7/7] Saving execution log...")
    duration = time.time() - start_time

    exec_log = {
        "execution_id": execution_id,
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "sources": ["pubmed", "openalex"],
        "max_requested": max_results,
        "total_retrieved": before_count,
        "after_dedup": after_count,
        "dedup_method": "doi + exact_title + fuzzy_title(>=90)",
        "evidence_grading": level_counts,
        "quality_grades": grades,
        "llm_summary": summary_count,
        "llm_provider": provider if do_summary else "none",
        "obsidian_export": obsidian_count,
        "zotero_sync": zotero_count,
        "prisma_diagram": prisma_path,
        "bibtex_file": bibtex_path,
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
    print(f"  Grades: {grades}")
    if do_summary:
        print(f"  Summaries: {summary_count}/{after_count}")
    print(f"  Output: {json_path}")
    if do_obsidian:
        print(f"  Obsidian: {obsidian_count} exported")
    if do_zotero:
        print(f"  Zotero: {zotero_count} synced")
    if prisma_path:
        print(f"  PRISMA: {prisma_path}")
    if bibtex_path:
        print(f"  BibTeX: {bibtex_path}")
    print("=" * 60)

    return 0


# ============================================================
# Pipeline steps
# ============================================================

def _step_search(query: str, max_results: int) -> list[dict]:
    """Search papers using UnifiedSourceClient or fallback."""
    try:
        from jarvis_core.sources import UnifiedSourceClient
        client = UnifiedSourceClient()
        from jarvis_core.sources.unified_source_client import SourceType
        sources = [SourceType.PUBMED, SourceType.OPENALEX]
        unified_papers = client.search(query, max_results=max_results, sources=sources)
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
    """Remove duplicate papers (DOI + exact title + fuzzy title)."""
    try:
        from rapidfuzz import fuzz
        has_rapidfuzz = True
    except ImportError:
        has_rapidfuzz = False

    seen_doi = set()
    seen_titles = []
    unique = []

    for p in papers:
        doi = (p.get("doi") or "").strip().lower()
        title = (p.get("title") or "").strip().lower()

        if doi and doi in seen_doi:
            continue
        if title and title in seen_titles:
            if doi:
                seen_doi.add(doi)
            continue
        if has_rapidfuzz and title:
            is_fuzzy_dup = False
            for existing_title in seen_titles:
                if fuzz.ratio(title, existing_title) >= 90:
                    is_fuzzy_dup = True
                    break
            if is_fuzzy_dup:
                if doi:
                    seen_doi.add(doi)
                continue

        if doi:
            seen_doi.add(doi)
        if title:
            seen_titles.append(title)
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
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        grade = grade_evidence(title=title, abstract=abstract, use_llm=False)
        level_val = grade.level.value if grade.level else "unknown"
        study_val = grade.study_type.value if grade.study_type else "unknown"
        conf = grade.confidence
        if level_val == "unknown":
            level_val, study_val, conf = _fallback_classify(title, abstract)
        p["evidence_level"] = level_val
        p["evidence_confidence"] = conf
        p["study_type"] = study_val

    return papers


def _step_scoring(papers: list[dict]) -> list[dict]:
    """Calculate quality score for each paper (B-3)."""
    try:
        from jarvis_cli.score import score_papers
        return score_papers(papers)
    except Exception as e:
        print(f"  Warning: Scoring failed: {e}")
        return papers


def _step_summarize(papers: list[dict], provider: str = "gemini") -> tuple[list[dict], int]:
    """Generate Japanese summary for each paper using LLM (A-1)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    try:
        from jarvis_core.llm import LLMClient, Message
    except ImportError:
        print("  Warning: LLMClient not available. Skipping summaries.")
        return papers, 0

    try:
        llm = LLMClient(provider=provider)
    except Exception as e:
        print(f"  Warning: Failed to initialize LLM ({provider}): {e}")
        return papers, 0

    success_count = 0
    for i, p in enumerate(papers):
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        if not abstract:
            p["summary_ja"] = f"（アブストラクト未取得: {title[:50]}）"
            continue
        print(f"  [{i+1}/{len(papers)}] {title[:55]}...")
        system_prompt = (
            "あなたは医学・生命科学の文献レビュー専門家です。\n"
            "以下の論文のタイトルとアブストラクトを読み、日本語で3〜5文の要約を作成してください。\n"
            "要約のみを出力し、他の説明は不要です。"
        )
        user_prompt = f"Title: {title}\n\nAbstract: {abstract}"
        try:
            raw = llm.chat([
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ])
            summary = raw.strip()
            if summary:
                p["summary_ja"] = summary
                success_count += 1
            else:
                p["summary_ja"] = "（要約生成失敗: 空の応答）"
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"    Rate limit hit. Waiting 40s and retrying...")
                time.sleep(40)
                try:
                    raw = llm.chat([
                        Message(role="system", content=system_prompt),
                        Message(role="user", content=user_prompt),
                    ])
                    summary = raw.strip()
                    if summary:
                        p["summary_ja"] = summary
                        success_count += 1
                    else:
                        p["summary_ja"] = "（要約生成失敗: 空の応答）"
                except Exception as e2:
                    p["summary_ja"] = f"（要約生成失敗: {e2}）"
            else:
                p["summary_ja"] = f"（要約生成失敗: {e}）"
        time.sleep(4)

    return papers, success_count


def _step_prisma(json_path: str, log_dir: Path, base_name: str) -> str:
    """Generate PRISMA 2020 flow diagram (A-4)."""
    try:
        import types
        from jarvis_cli.prisma import run_prisma
        prisma_output = str(log_dir / f"{base_name}_prisma.md")
        mock_args = types.SimpleNamespace(files=[json_path], output=prisma_output)
        result = run_prisma(mock_args)
        if result == 0:
            return prisma_output
        return ""
    except Exception as e:
        print(f"  Warning: PRISMA generation failed: {e}")
        return ""


def _step_bibtex(papers: list[dict], log_dir: Path, base_name: str) -> str:
    """Export papers as BibTeX file (A-5)."""
    try:
        from jarvis_cli.bibtex import save_bibtex
        bib_path = log_dir / f"{base_name}.bib"
        save_bibtex(papers, bib_path)
        return str(bib_path)
    except Exception as e:
        print(f"  Warning: BibTeX export failed: {e}")
        return ""


def _fallback_classify(title: str, abstract: str) -> tuple:
    """Simple keyword-based fallback for evidence classification."""
    text = (title + " " + abstract).lower()
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
    """Sync papers to Zotero (C-6: with collection support)."""
    try:
        from jarvis_cli.zotero_sync import _get_zotero_client, _build_zotero_item
        from jarvis_cli.zotero_sync import _get_crossref_metadata, _get_doi_from_crossref
        from jarvis_cli.zotero_sync import _load_config, _get_or_create_collection
        import time as _time
        zot = _get_zotero_client()
        if zot is None:
            return 0
        config = _load_config()
        collection_name = config.get("zotero", {}).get("collection", "")
        collection_key = None
        if collection_name:
            collection_key = _get_or_create_collection(zot, collection_name)
        count = 0
        for p in papers:
            doi = p.get("doi") or p.get("DOI")
            if not doi:
                doi = _get_doi_from_crossref(p.get("title", ""))
            if not doi:
                continue
            try:
                meta = _get_crossref_metadata(doi)
                item = _build_zotero_item(zot, doi, meta, collection_key=collection_key)
                zot.create_items([item])
                count += 1
            except Exception:
                pass
            _time.sleep(1)
        return count
    except Exception as e:
        print(f"  Warning: Zotero sync failed: {e}")
        return 0
