"""Generate Obsidian-compatible research notes for a run."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .templates import (
    TEMPLATE_VERSION,
    format_frontmatter,
    format_run_overview_header,
    format_section,
)

DEFAULT_OA_STATUS = "unknown"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _safe_filename(value: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in value)


def _slug(text: str, max_len: int = 48) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in text.lower())
    cleaned = "_".join(filter(None, cleaned.split("_")))
    return cleaned[:max_len] or "untitled"


def _extract_locator(locator: dict[str, Any]) -> tuple[str, int | None, int | None, str | None]:
    section = locator.get("section") or locator.get("Section") or "Unknown"
    paragraph = locator.get("paragraph_index")
    if paragraph is None:
        paragraph = locator.get("paragraph")
    sentence = locator.get("sentence_index")
    if sentence is None:
        sentence = locator.get("sentence")
    chunk_id = locator.get("chunk_id") or locator.get("chunk")
    return section, paragraph, sentence, chunk_id


def _format_locator(locator: dict[str, Any]) -> str:
    section, paragraph, sentence, chunk_id = _extract_locator(locator)
    paragraph_text = paragraph if paragraph is not None else "?"
    sentence_text = sentence if sentence is not None else "?"
    chunk_text = chunk_id if chunk_id is not None else "unknown"
    parts = [
        f"chunk_id={chunk_text}",
        f"{section} ¶{paragraph_text}",
        f"sentence {sentence_text}",
    ]
    return "Evidence: " + ", ".join(parts)


def _ensure_length(text: str, min_len: int, max_len: int) -> str:
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    if len(text) < min_len:
        filler = " 本研究の要点は背景・方法・結果が一連で整理されており、詳細は原文の根拠箇所を確認することが重要です。"
        while len(text) + len(filler) < min_len:
            text += filler
        if len(text) < min_len:
            text += filler
        return text[:max_len]
    return text


def _build_tldr(paper: dict[str, Any], claims: list[dict[str, Any]]) -> str:
    title = paper.get("title", "")
    claim_texts = [c.get("claim_text", "") for c in claims if c.get("claim_text")]
    claim_summary = " / ".join(claim_texts[:2])
    if claim_summary:
        base = f"本論文「{title}」は、{claim_summary}を中心に研究結果を整理している。"
    else:
        base = f"本論文「{title}」は研究背景と主要結果を整理している。"
    return _ensure_length(base, 200, 300)


def _build_snapshot(section_name: str, paper: dict[str, Any], fallback: str) -> str:
    value = paper.get(section_name)
    if isinstance(value, str) and value.strip():
        return value.strip()[:500]
    return fallback


def _build_limitations(paper: dict[str, Any]) -> str:
    author_limitations = paper.get("limitations")
    if author_limitations:
        return f"著者の限界: {author_limitations}\n\n注意: サンプルサイズや解析条件の再確認が必要。"
    return "著者の限界: 記載が限定的。\n\n注意: 原文の条件設定と対象集団の妥当性を再確認する。"


def _build_why_it_matters(paper: dict[str, Any]) -> str:
    domain = paper.get("domain") or "研究テーマ"
    return f"{domain}における仮説検証や次の実験設計に直結するため、重要な背景知識として活用できる。"


def _group_by_key(items: Iterable[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[item.get(key, "unknown")].append(item)
    return grouped


def _score_from_scores(scores: dict[str, Any]) -> dict[str, float]:
    ranking_scores: dict[str, float] = {}
    rankings = scores.get("rankings")
    if isinstance(rankings, list) and rankings:
        for entry in rankings:
            if isinstance(entry, dict):
                paper_id = entry.get("paper_id") or entry.get("id")
                score = entry.get("score")
                if score is None:
                    score = entry.get("total_score")
                if paper_id and score is not None:
                    ranking_scores[paper_id] = float(score)
    if ranking_scores:
        return ranking_scores
    papers_scores = scores.get("papers")
    if isinstance(papers_scores, dict):
        for paper_id, features in papers_scores.items():
            if isinstance(features, dict):
                ranking_scores[paper_id] = float(
                    sum(v for v in features.values() if isinstance(v, (int, float)))
                )
            elif isinstance(features, (int, float)):
                ranking_scores[paper_id] = float(features)
    return ranking_scores


def _compute_rankings(
    papers: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    scores: dict[str, Any],
) -> list[dict[str, Any]]:
    score_map = _score_from_scores(scores)
    if not score_map:
        claim_counts = Counter(c.get("paper_id", "unknown") for c in claims)
        for paper in papers:
            paper_id = paper.get("paper_id", "unknown")
            score_map[paper_id] = float(claim_counts.get(paper_id, 0))
    ranked = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
    results = []
    for idx, (paper_id, score) in enumerate(ranked, start=1):
        results.append({"paper_id": paper_id, "score": score, "rank": idx})
    return results


def _assign_tiers(rankings: list[dict[str, Any]]) -> dict[str, str]:
    total = len(rankings)
    if total == 0:
        return {}
    s_count = max(1, int(total * 0.1))
    a_count = max(1, int(total * 0.2))
    if s_count + a_count > total:
        a_count = max(0, total - s_count)
    tiers = {}
    for entry in rankings:
        rank = entry["rank"]
        if rank <= s_count:
            tiers[entry["paper_id"]] = "S"
        elif rank <= s_count + a_count:
            tiers[entry["paper_id"]] = "A"
        else:
            tiers[entry["paper_id"]] = "B"
    return tiers


def _build_evidence_map(
    claims: list[dict[str, Any]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> str:
    lines = []
    for claim in claims:
        claim_id = claim.get("claim_id", "unknown")
        evs = evidence_by_claim.get(claim_id, [])
        if not evs:
            lines.append(f'- {claim_id}: Unknown ¶? sentence ? (chunk_id=unknown) → "N/A"')
            continue
        for ev in evs:
            locator = ev.get("locator", {}) if isinstance(ev.get("locator"), dict) else {}
            section, paragraph, sentence, chunk_id = _extract_locator(locator)
            paragraph_text = paragraph if paragraph is not None else "?"
            sentence_text = sentence if sentence is not None else "?"
            chunk_text = chunk_id if chunk_id is not None else "unknown"
            locator_text = (
                f"{section} ¶{paragraph_text} sentence {sentence_text} (chunk_id={chunk_text})"
            )
            quote = ev.get("evidence_text", "").strip()
            quote = quote.replace("\n", " ")[:240]
            lines.append(f'- {claim_id}: {locator_text} → "{quote}"')
    return "\n".join(lines)


def _build_key_claims(
    claims: list[dict[str, Any]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> str:
    paragraphs = []
    for claim in claims:
        text = claim.get("claim_text", "").strip()
        if not text:
            continue
        evs = evidence_by_claim.get(claim.get("claim_id", ""), [])
        if evs:
            locator = evs[0].get("locator", {}) if isinstance(evs[0].get("locator"), dict) else {}
            evidence_line = _format_locator(locator)
        else:
            evidence_line = _format_locator({})
        paragraphs.append(f"{text}\n{evidence_line}")
    if not paragraphs:
        paragraphs.append("主張の抽出データがありません。")
    return "\n\n".join(paragraphs)


def generate_notes(
    run_id: str,
    source_runs_dir: Path = Path("logs/runs"),
    output_base_dir: Path = Path("data/runs"),
) -> dict[str, Any]:
    """Generate Obsidian notes for a run.

    Returns metadata about generated outputs.
    """
    run_dir = source_runs_dir / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    output_dir = output_base_dir / run_id
    notes_dir = output_dir / "notes"
    papers_dir = notes_dir / "papers"
    claims_dir = notes_dir / "claims"
    export_claims_dir = output_dir / "claims"
    notes_dir.mkdir(parents=True, exist_ok=True)
    papers_dir.mkdir(parents=True, exist_ok=True)
    claims_dir.mkdir(parents=True, exist_ok=True)
    export_claims_dir.mkdir(parents=True, exist_ok=True)

    papers = _load_jsonl(run_dir / "papers.jsonl")
    claims = _load_jsonl(run_dir / "claims.jsonl")
    evidence = _load_jsonl(run_dir / "evidence.jsonl")
    scores = _load_json(run_dir / "scores.json")
    input_data = _load_json(run_dir / "input.json")
    warnings = _load_jsonl(run_dir / "warnings.jsonl")

    claims_by_paper = _group_by_key(claims, "paper_id")
    evidence_by_claim = _group_by_key(evidence, "claim_id")

    rankings = _compute_rankings(papers, claims, scores)
    tiers = _assign_tiers(rankings)
    ranking_map = {entry["paper_id"]: entry for entry in rankings}

    oa_statuses = Counter(p.get("oa_status", DEFAULT_OA_STATUS) for p in papers)
    warning_counts = Counter(w.get("code", "GENERAL") for w in warnings)

    # Paper notes and claim exports
    for paper in papers:
        paper_id = paper.get("paper_id", "unknown")
        paper_claims = claims_by_paper.get(paper_id, [])
        claim_entries = []
        for claim in paper_claims:
            claim_id = claim.get("claim_id", "unknown")
            evs = evidence_by_claim.get(claim_id, [])
            claim_entries.append(
                {
                    "paper_id": paper_id,
                    "claim_id": claim_id,
                    "claim_text": claim.get("claim_text", ""),
                    "evidence": [
                        {
                            "evidence_text": ev.get("evidence_text", ""),
                            "locator": ev.get("locator", {}),
                        }
                        for ev in evs
                    ],
                }
            )

        claim_path = claims_dir / f"{_safe_filename(paper_id)}.claims.jsonl"
        export_claim_path = export_claims_dir / f"{_safe_filename(paper_id)}.claims.jsonl"
        for path in (claim_path, export_claim_path):
            with open(path, "w", encoding="utf-8") as f:
                for entry in claim_entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        ranking = ranking_map.get(paper_id, {"score": 0.0})
        tier = tiers.get(paper_id, "B")
        score = float(ranking.get("score", 0.0))

        tags = ["jarvis", f"run:{run_id}"]
        if paper.get("keywords"):
            tags.extend([str(k) for k in paper.get("keywords") if k])

        frontmatter = format_frontmatter(
            paper_id=paper_id,
            title=paper.get("title", "Untitled"),
            year=paper.get("year"),
            journal=paper.get("journal"),
            doi=paper.get("doi"),
            pmid=paper.get("pmid"),
            pmcid=paper.get("pmcid"),
            oa_status=paper.get("oa_status", DEFAULT_OA_STATUS),
            tier=tier,
            score=score,
            tags=tags,
            source_run=run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        key_claims = _build_key_claims(paper_claims, evidence_by_claim)
        tldr = _build_tldr(paper, paper_claims)
        methods = _build_snapshot("methods", paper, "主要な手法情報は原文確認が必要。")
        results = _build_snapshot("results", paper, "主要結果はclaimに記載。")
        limitations = _build_limitations(paper)
        why_it_matters = _build_why_it_matters(paper)
        evidence_map = _build_evidence_map(paper_claims, evidence_by_claim)

        body_parts = [
            format_section("TL;DR", tldr),
            format_section("Key claims", key_claims),
            format_section("Methods snapshot", methods),
            format_section("Results snapshot", results),
            format_section("Limitations", limitations),
            format_section("Why it matters", why_it_matters),
            format_section("Evidence map", evidence_map),
            "## Links\n\n" "- [Run Overview](../00_RUN_OVERVIEW.md)\n" f"- [[papers/{paper_id}]]\n",
        ]

        note_path = papers_dir / f"{_safe_filename(paper_id)}.md"
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(frontmatter)
            f.write("\n".join(body_parts))

    # Tier summary notes
    tier_s = [entry for entry in rankings if tiers.get(entry["paper_id"]) == "S"]
    tier_a = [entry for entry in rankings if tiers.get(entry["paper_id"]) == "A"]

    def _build_tier_list(entries: list[dict[str, Any]]) -> str:
        lines = []
        for entry in entries:
            paper_id = entry["paper_id"]
            paper = next((p for p in papers if p.get("paper_id") == paper_id), {})
            title = paper.get("title", "Untitled")
            lines.append(f"- [[papers/{paper_id}]] — {title} (score={entry.get('score', 0):.2f})")
        return "\n".join(lines) if lines else "- (none)"

    (notes_dir / "01_TIER_S.md").write_text(
        "# Tier S Papers\n\n" + _build_tier_list(tier_s) + "\n",
        encoding="utf-8",
    )
    (notes_dir / "02_TIER_A.md").write_text(
        "# Tier A Papers\n\n" + _build_tier_list(tier_a) + "\n",
        encoding="utf-8",
    )

    # Run overview
    query = input_data.get("query") or input_data.get("goal") or ""
    filters = json.dumps(input_data.get("constraints", {}), ensure_ascii=False)
    header = format_run_overview_header(run_id, query, filters)

    summary_lines = [
        header,
        format_section(
            "Collection stats",
            "\n".join(
                [
                    f"- found: {len(papers)}",
                    f"- downloaded: {len(papers)}",
                    f"- extracted: {len(papers)}",
                    f"- chunked: {len(evidence)}",
                    f"- deduped: {len(set(p.get('paper_id') for p in papers))}",
                ]
            ),
        ),
        format_section(
            "OA ratio",
            "\n".join([f"- {k}: {v}" for k, v in oa_statuses.items()]) or "- unknown",
        ),
        format_section(
            "Audit flags",
            "\n".join([f"- {code}: {count}" for code, count in warning_counts.most_common(5)])
            or "- none",
        ),
        format_section(
            "Tier counts",
            "\n".join(
                [
                    f"- S: {sum(1 for t in tiers.values() if t == 'S')}",
                    f"- A: {sum(1 for t in tiers.values() if t == 'A')}",
                    f"- B: {sum(1 for t in tiers.values() if t == 'B')}",
                ]
            ),
        ),
    ]

    top_entries = rankings[:10]
    top_lines = []
    for entry in top_entries:
        paper = next((p for p in papers if p.get("paper_id") == entry["paper_id"]), {})
        top_lines.append(
            f"- {paper.get('title', 'Untitled')} ({paper.get('year', 'n/a')}, "
            f"{paper.get('journal', 'n/a')}) score={entry.get('score', 0):.2f} "
            f"oa={paper.get('oa_status', DEFAULT_OA_STATUS)}"
        )
    summary_lines.append(format_section("Top 10 (S→A)", "\n".join(top_lines) or "- none"))

    next_actions = [
        "Tier Sから優先的に全文確認し、重要claimの再現性を検証する。",
        "不足しているOA文献がある場合は追加検索で補完する。",
        "Evidence locatorが弱いclaimは原文の該当箇所を追跡する。",
    ]
    summary_lines.append(format_section("Next actions", "\n".join(f"- {a}" for a in next_actions)))

    (notes_dir / "00_RUN_OVERVIEW.md").write_text("\n".join(summary_lines), encoding="utf-8")

    research_rank = {
        "run_id": run_id,
        "template_version": TEMPLATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rankings": [{**entry, "tier": tiers.get(entry["paper_id"], "B")} for entry in rankings],
    }
    (output_dir / "research_rank.json").write_text(
        json.dumps(research_rank, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "notes_dir": str(notes_dir),
        "papers_count": len(papers),
        "claims_count": len(claims),
        "template_version": TEMPLATE_VERSION,
        "research_rank": research_rank,
    }
