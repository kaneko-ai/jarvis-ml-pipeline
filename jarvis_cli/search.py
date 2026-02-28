"""jarvis search - lightweight paper search (P1-1 + P1-3 + P3 codex + v2 unified)."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from jarvis_cli.bibtex import save_bibtex


# ---------------------------------------------------------------------------
# ★ v2追加: ソース名の文字列 → SourceType 列挙値 への変換マップ
#
#   ユーザーがコマンドラインで指定する短い名前（左側）を、
#   jarvis_core が内部で使う SourceType 列挙値の名前（右側）に対応付けます。
#   例: "s2" → "SEMANTIC_SCHOLAR"
# ---------------------------------------------------------------------------
_SOURCE_NAME_MAP: dict[str, str] = {
    "pubmed": "PUBMED",
    "s2": "SEMANTIC_SCHOLAR",
    "semantic_scholar": "SEMANTIC_SCHOLAR",
    "openalex": "OPENALEX",
}


def _parse_sources(sources_str: str | None):
    """カンマ区切りのソース指定文字列を SourceType のリストに変換する。

    Args:
        sources_str: "pubmed,s2,openalex" のようなカンマ区切り文字列。
                     None の場合は None を返す（＝従来の PubMed のみ動作）。

    Returns:
        SourceType のリスト、または None。

    使用例:
        _parse_sources("pubmed,s2")
        → [SourceType.PUBMED, SourceType.SEMANTIC_SCHOLAR]

        _parse_sources(None)
        → None
    """
    if sources_str is None:
        return None

    # ここで初めて jarvis_core をインポートする（遅延インポート）。
    # 理由: --sources を使わない場合は jarvis_core.sources を読み込まなくて済むため。
    from jarvis_core.sources.unified_source_client import SourceType

    result = []
    for name in sources_str.split(","):
        name = name.strip().lower()
        if name in _SOURCE_NAME_MAP:
            enum_name = _SOURCE_NAME_MAP[name]
            result.append(SourceType[enum_name])
        else:
            available = ", ".join(sorted(_SOURCE_NAME_MAP.keys()))
            print(
                f"  Warning: Unknown source '{name}' (skipping). "
                f"Available sources: {available}"
            )

    return result if result else None


def _search_with_unified_client(query: str, max_results: int, sources):
    """UnifiedSourceClient を使って複数ソースから統合検索する。

    Args:
        query: 検索クエリ（例: "PD-1 immunotherapy"）
        max_results: 各ソースから取得する最大件数
        sources: SourceType のリスト

    Returns:
        (papers, warnings) のタプル。
        papers は既存の dict 形式（_print_papers 等が期待するフォーマット）のリスト。
        warnings は警告メッセージのリスト。
    """
    from jarvis_core.sources.unified_source_client import UnifiedSourceClient

    source_names = [s.value for s in sources]
    print(f"  Unified search mode: {source_names}")
    print(f"  Max {max_results} papers per source, with DOI deduplication")

    # UnifiedSourceClient はコンストラクタ引数で email や API キーを
    # 受け取れるが、現時点では省略してデフォルトで動かす。
    client = UnifiedSourceClient()

    # 統合検索を実行（ソースごとに順次呼び出し → DOI で重複除去）
    unified_papers = client.search(
        query=query,
        max_results=max_results,
        sources=sources,
        deduplicate=True,
    )

    warnings: list[str] = []

    # UnifiedPaper オブジェクトを、既存 CLI が使っている dict 形式に変換する。
    # こうすることで、_print_papers(), _build_report_md(), save_bibtex() など
    # 既存の関数をそのまま使える。
    papers: list[dict] = []
    for up in unified_papers:
        paper_dict = {
            "title": up.title,
            "abstract": up.abstract,
            "authors": up.authors,
            "year": up.year,
            "journal": up.venue,           # UnifiedPaper では venue
            "doi": up.doi,
            "pmid": up.pmid,
            "source": up.source.value,     # "pubmed", "semantic_scholar", "openalex"
            "source_id": up.id,            # "pubmed:12345", "s2:abcde" etc.
            "url": up.url or "",
            "citation_count": up.citation_count,
            "keywords": up.keywords,
        }
        papers.append(paper_dict)

    if not papers:
        warnings.append(f"No papers found from any source for '{query}'.")
    else:
        print(f"  Retrieved {len(papers)} unique papers (after deduplication)")

    return papers, warnings


def _search_with_legacy(query: str, max_results: int):
    """従来の PubMed のみ検索（既存動作の維持）。

    Args:
        query: 検索クエリ
        max_results: 最大件数

    Returns:
        (papers, warnings) のタプル。
    """
    from jarvis_core.agents import PaperFetcherAgent

    agent = PaperFetcherAgent()
    papers, warnings = agent._search_papers(query=query, max_results=max_results)
    return papers, warnings


def run_search(args):
    """search command main logic.

    --sources が指定されていれば UnifiedSourceClient で複数ソース検索。
    指定がなければ従来通り PubMed のみ検索。
    """
    query = args.query.strip()
    max_results = max(1, min(args.max_results, 20))
    provider = getattr(args, "provider", "gemini")
    sources = _parse_sources(getattr(args, "sources", None))

    if not query:
        print("Error: search query is empty.", file=sys.stderr)
        return 1

    print(f"Searching for: '{query}' (max {max_results} papers)...")
    if provider != "gemini":
        print(f"  LLM provider: {provider}")
    print()

    # ------------------------------------------------------------------
    # 検索の実行
    # ------------------------------------------------------------------
    start_time = time.perf_counter()

    if sources is not None:
        # ★ v2: UnifiedSourceClient による統合検索
        papers, warnings = _search_with_unified_client(query, max_results, sources)
    else:
        # 従来動作: PubMed のみ
        papers, warnings = _search_with_legacy(query, max_results)

    search_duration = time.perf_counter() - start_time

    if not papers:
        print(f"No papers found for '{query}'.")
        if warnings:
            for w in warnings:
                print(f"  Warning: {w}")
        return 1

    print(f"Found {len(papers)} papers in {search_duration:.1f}s")

    # ------------------------------------------------------------------
    # LLM による日本語要約（--no-summary が指定されていなければ実行）
    # ------------------------------------------------------------------
    if not args.no_summary:
        print(f"Adding LLM summaries via {provider} (may take a moment)...")
        try:
            from jarvis_core.agents import PaperFetcherAgent
            from jarvis_core.llm import LLMClient

            llm = LLMClient(provider=provider)
            agent = PaperFetcherAgent()
            papers = agent._enrich_papers_with_llm(llm, papers)
            print("Done.")
        except Exception as e:
            print(f"Warning: LLM summary failed ({provider}): {e}")
            print("Continuing without summaries.")
    print()

    # ------------------------------------------------------------------
    # 結果の表示
    # ------------------------------------------------------------------
    if args.json_output:
        print(json.dumps(papers, ensure_ascii=False, indent=2))
    else:
        _print_papers(papers)

    # ------------------------------------------------------------------
    # ファイルへの保存
    # ------------------------------------------------------------------
    output_path = _get_output_path(args.output, query, args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.json_output:
        output_path.write_text(
            json.dumps(papers, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        md = _build_report_md(query, papers, warnings, search_duration)
        output_path.write_text(md, encoding="utf-8")

    # BibTeX output (P1-3)
    if getattr(args, "bibtex", False):
        bib_path = output_path.with_suffix(".bib")
        save_bibtex(papers, bib_path)
        print(f"BibTeX saved to: {bib_path}")

    print()
    print(f"Report saved to: {output_path}")

    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")

    return 0


# ======================================================================
# 以下は既存の関数（変更なし）
# ======================================================================


def _print_papers(papers):
    """Print papers to terminal."""
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "n.d.")
        source = p.get("source", "?")
        journal = p.get("journal", "")
        evidence = p.get("evidence_level", "")
        summary = p.get("summary_ja", "")

        print(f"[{i}] {title}")
        print(f"    Year: {year} | Source: {source}", end="")
        if journal:
            print(f" | Journal: {journal}", end="")
        print()
        if evidence and evidence != "N/A":
            print(f"    CEBM Level: {evidence}")
        if summary:
            print(f"    Summary: {summary}")
        print()


def _get_output_path(user_path, query, is_json):
    """Decide output file path."""
    if user_path:
        return Path(user_path)

    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in query)
    safe = safe.strip("_")[:30]
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "json" if is_json else "md"
    return Path("logs") / "search" / f"{safe}_{date_str}.{ext}"


def _build_report_md(query, papers, warnings, duration):
    """Build a Markdown report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Paper Search: {query}",
        "",
        f"**Date:** {now}",
        f"**Papers found:** {len(papers)}",
        f"**Search time:** {duration:.1f}s",
        "",
        "---",
        "",
    ]

    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "n.d.")
        authors = p.get("authors", [])
        journal = p.get("journal", "")
        source = p.get("source", "")
        doi = p.get("doi", "")
        pmid = p.get("pmid", "")
        url = p.get("url", "")
        evidence = p.get("evidence_level", "")
        summary = p.get("summary_ja", "")
        abstract = p.get("abstract", "")

        lines.append(f"## {i}. {title}")
        lines.append("")

        if authors:
            author_str = ", ".join(authors[:5])
            if len(authors) > 5:
                author_str += f" et al. ({len(authors)} authors)"
            lines.append(f"**Authors:** {author_str}")
        lines.append(f"**Year:** {year}")
        if journal:
            lines.append(f"**Journal:** {journal}")
        lines.append(f"**Source:** {source}")
        if evidence and evidence != "N/A":
            lines.append(f"**CEBM Evidence Level:** {evidence}")
        lines.append("")

        link_parts = []
        if url:
            link_parts.append(f"[Link]({url})")
        if doi:
            link_parts.append(f"[DOI](https://doi.org/{doi})")
        if pmid:
            link_parts.append(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
        if link_parts:
            lines.append(" | ".join(link_parts))
            lines.append("")

        if summary:
            lines.append("### Summary (Japanese)")
            lines.append("")
            lines.append(summary)
            lines.append("")

        if abstract:
            lines.append("<details>")
            lines.append("<summary>Abstract (English)</summary>")
            lines.append("")
            lines.append(abstract)
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append("## References")
    lines.append("")
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        authors = p.get("authors", [])
        year = p.get("year", "n.d.")
        journal = p.get("journal", "")
        doi = p.get("doi", "")
        a_str = ", ".join(authors[:3])
        if len(authors) > 3:
            a_str += " et al."
        ref = f"{i}. {a_str} ({year}). {title}. {journal}."
        if doi:
            ref += f" doi:{doi}"
        lines.append(ref)
        lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append(f"*Generated by JARVIS Research OS on {now}*")
    return "\n".join(lines)
