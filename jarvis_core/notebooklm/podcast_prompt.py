"""Generate NotebookLM podcast prompts and outlines."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis_core.notes.note_generator import (
    _assign_tiers,
    _compute_rankings,
    _format_locator,
    _load_json,
    _load_jsonl,
)

VOCAB_GUIDE = "高校生〜学部生が説明できる語彙で、重要語は英語併記すること。"


def _claim_lines(
    claims: list[dict[str, Any]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> list[str]:
    lines = []
    for claim in claims:
        text = claim.get("claim_text", "").strip()
        if not text:
            continue
        evs = evidence_by_claim.get(claim.get("claim_id", ""), [])
        locator_text = _format_locator({})
        if evs:
            locator = evs[0].get("locator", {}) if isinstance(evs[0].get("locator"), dict) else {}
            locator_text = _format_locator(locator)
        lines.append(f"- 【事実】{text}\n  {locator_text}")
    return lines or ["- 【事実】claim抽出がありません。"]


def build_single_paper_prompt(
    paper: dict[str, Any],
    claims: list[dict[str, Any]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> str:
    title = paper.get("title", "Untitled")
    return "\n".join(
        [
            f"# Podcast Prompt: {title}",
            "",
            VOCAB_GUIDE,
            "",
            "## 目的",
            "- 1本の論文を深掘りし、背景→方法→結果→意義を説明する",
            "",
            "## 要約ポイント",
            f"- 研究テーマ: {title}",
            f"- ジャーナル: {paper.get('journal', 'n/a')}",
            f"- 年: {paper.get('year', 'n/a')}",
            "",
            "## 主張と根拠",
            *(_claim_lines(claims, evidence_by_claim)),
            "",
            "## 説明フロー",
            "1. 背景と研究の問い (background / question)",
            "2. 方法の概要 (methods) - 重要語は英語併記",
            "3. 結果と意味 (results / implications)",
            "4. 限界と今後 (limitations / next steps)",
            "",
            "## 注意",
            "- 【事実】と【解釈】を明確に区別する",
            "- Evidence locatorを必ず含める",
        ]
    )


def build_multi_paper_prompt(
    papers: list[dict[str, Any]],
    claims_by_paper: dict[str, list[dict[str, Any]]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> str:
    lines = [
        "# Podcast Prompt: 3-5 Papers Synthesis",
        "",
        VOCAB_GUIDE,
        "",
        "## 目的",
        "- 3〜5本の論文を統合して主要論点を説明する",
        "",
        "## 論文リスト",
    ]

    for paper in papers:
        paper_id = paper.get("paper_id", "unknown")
        lines.append(f"- {paper.get('title', 'Untitled')} ({paper.get('year', 'n/a')})")
        claims = claims_by_paper.get(paper_id, [])
        lines.extend(_claim_lines(claims, evidence_by_claim))

    lines.extend(
        [
            "",
            "## 統合ストーリー",
            "1. 共通する背景と課題",
            "2. 方法の違いと共通点",
            "3. 主要な結果の比較",
            "4. 研究分野への示唆",
            "",
            "## 注意",
            "- Evidence locatorを必ず付ける",
            "- 推測は【解釈】で明示",
        ]
    )
    return "\n".join(lines)


def build_script_outline(
    papers: list[dict[str, Any]],
    claims_by_paper: dict[str, list[dict[str, Any]]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> str:
    lines = [
        "# Podcast Script Outline",
        "",
        "## Chapter 1: イントロ (Intro)",
        "- テーマと背景を短く説明",
        "",
        "## Chapter 2: コア論文解説 (Core Paper)",
    ]
    if papers:
        paper = papers[0]
        lines.append(f"- {paper.get('title', 'Untitled')}")
        claims = claims_by_paper.get(paper.get("paper_id", ""), [])
        lines.extend(_claim_lines(claims, evidence_by_claim))

    lines.extend(
        [
            "",
            "## Chapter 3: 比較と統合 (Comparison)",
            "- 各論文の結果比較と違い",
            "",
            "## Chapter 4: まとめ (Takeaways)",
            "- 重要ポイントの復習",
            "- 次の問い",
        ]
    )
    return "\n".join(lines)


def generate_notebooklm_outputs(
    run_id: str,
    source_runs_dir: Path = Path("logs/runs"),
    output_base_dir: Path = Path("data/runs"),
) -> dict[str, Any]:
    run_dir = source_runs_dir / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    output_dir = output_base_dir / run_id / "notebooklm"
    output_dir.mkdir(parents=True, exist_ok=True)

    papers = _load_jsonl(run_dir / "papers.jsonl")
    claims = _load_jsonl(run_dir / "claims.jsonl")
    evidence = _load_jsonl(run_dir / "evidence.jsonl")
    scores = _load_json(run_dir / "scores.json")

    claims_by_paper: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        claims_by_paper.setdefault(claim.get("paper_id", "unknown"), []).append(claim)

    evidence_by_claim: dict[str, list[dict[str, Any]]] = {}
    for ev in evidence:
        evidence_by_claim.setdefault(ev.get("claim_id", "unknown"), []).append(ev)

    rankings = _compute_rankings(papers, claims, scores)
    tiers = _assign_tiers(rankings)
    ranked_papers = [p for p in papers if tiers.get(p.get("paper_id", "")) in {"S", "A"}]
    if not ranked_papers:
        ranked_papers = papers

    single_paper = ranked_papers[0] if ranked_papers else {}
    multi_papers = ranked_papers[:5]

    prompt_single = build_single_paper_prompt(
        single_paper,
        claims_by_paper.get(single_paper.get("paper_id", ""), []),
        evidence_by_claim,
    )
    prompt_multi = build_multi_paper_prompt(
        multi_papers,
        claims_by_paper,
        evidence_by_claim,
    )
    outline = build_script_outline(multi_papers, claims_by_paper, evidence_by_claim)

    (output_dir / "podcast_prompt_1paper.txt").write_text(prompt_single, encoding="utf-8")
    (output_dir / "podcast_prompt_3to5papers.txt").write_text(prompt_multi, encoding="utf-8")
    (output_dir / "podcast_script_outline.md").write_text(outline, encoding="utf-8")

    return {
        "notebooklm_dir": str(output_dir),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "papers_count": len(papers),
    }
