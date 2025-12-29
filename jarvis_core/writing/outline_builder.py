"""Outline and draft structure builder for writing outputs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .citation_formatter import EvidenceLocator, format_evidence_locator, has_weak_evidence


@dataclass
class ClaimDatum:
    """Normalized claim information for drafting."""

    text: str
    evidence: List[EvidenceLocator]
    weak: bool = False
    score: Optional[float] = None
    claim_id: Optional[str] = None


@dataclass
class Section:
    """Draft section container."""

    title: str
    paragraphs: List[str]


def load_template(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _sorted_claims(claims: Iterable[ClaimDatum]) -> List[ClaimDatum]:
    claims_list = list(claims)
    scored = [c for c in claims_list if c.score is not None]
    if scored:
        return sorted(claims_list, key=lambda c: c.score or 0, reverse=True)
    return claims_list


def _paragraph_from_claim(claim: ClaimDatum, prefix: str | None = None) -> str:
    text = claim.text.strip()
    if prefix:
        text = f"{prefix}{text}"
    locator = format_evidence_locator(claim.evidence)
    weak_note = "（推測です）" if claim.weak or has_weak_evidence(claim.evidence) else ""
    return f"{text} {locator}{weak_note}".strip()


def _fallback_paragraph(label: str) -> str:
    locator = format_evidence_locator([])
    return f"{label} {locator}"


def build_research_plan_sections(
    claims: Iterable[ClaimDatum],
    overview_text: str,
    references: List[str],
) -> List[Section]:
    ordered = _sorted_claims(claims)
    top_claim = ordered[0] if ordered else None

    overview_paragraphs = [p.strip() for p in overview_text.split("\n\n") if p.strip()]
    if overview_paragraphs and top_claim:
        background_paragraphs = [
            f"{overview_paragraphs[0]} {format_evidence_locator(top_claim.evidence)}"
            f"{'（推測です）' if top_claim.weak else ''}"
        ]
    elif top_claim:
        background_paragraphs = [_paragraph_from_claim(top_claim, prefix="背景: ")]
    else:
        background_paragraphs = [_fallback_paragraph("背景情報は追加予定です。")]

    gap_claim = ordered[1] if len(ordered) > 1 else top_claim
    gap_paragraphs = (
        [_paragraph_from_claim(gap_claim, prefix="未解決課題: ")] if gap_claim else [_fallback_paragraph("未解決課題を整理してください。")]
    )

    hypothesis_claim = ordered[2] if len(ordered) > 2 else top_claim
    hypothesis_paragraphs = (
        [_paragraph_from_claim(hypothesis_claim, prefix="仮説: ")] if hypothesis_claim else [_fallback_paragraph("仮説を設定してください。")]
    )

    aim_paragraphs: List[str] = []
    for idx in range(3):
        if idx < len(ordered):
            aim_paragraphs.append(_paragraph_from_claim(ordered[idx], prefix=f"Aim {idx + 1}: "))
        else:
            aim_paragraphs.append(_fallback_paragraph(f"Aim {idx + 1}: [[YOUR_DATA_HERE]]"))

    approach_paragraphs: List[str] = []
    for idx in range(3):
        claim = ordered[idx] if idx < len(ordered) else top_claim
        if claim:
            approach_paragraphs.append(
                _paragraph_from_claim(claim, prefix=f"Aim {idx + 1}の方法: [[YOUR_DATA_HERE]] ")
            )
        else:
            approach_paragraphs.append(_fallback_paragraph(f"Aim {idx + 1}の方法: [[YOUR_DATA_HERE]]"))

    expected_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="期待される結果: ")]
        if top_claim
        else [_fallback_paragraph("期待される結果を記述してください。")]
    )

    risk_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="リスク: [[LAB_TERMS_CHECK]] ")]
        if top_claim
        else [_fallback_paragraph("リスクと代替案を追記してください。")]
    )

    impact_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="インパクト: ")]
        if top_claim
        else [_fallback_paragraph("インパクトを記述してください。")]
    )

    reference_paragraphs = [
        f"- {ref}" for ref in references
    ] or ["- [[REFERENCES_PLACEHOLDER]]"]

    return [
        Section("背景 (Background)", background_paragraphs),
        Section("未解決課題 (Gap)", gap_paragraphs),
        Section("仮説 (Hypothesis)", hypothesis_paragraphs),
        Section("目的 (Aims)", aim_paragraphs),
        Section("研究方法 (Approach)", approach_paragraphs),
        Section("期待される結果と解釈 (Expected outcomes)", expected_paragraphs),
        Section("リスクと代替案 (Risks & Alternatives)", risk_paragraphs),
        Section("インパクト (Impact)", impact_paragraphs),
        Section("参考文献 (References)", reference_paragraphs),
    ]


def build_thesis_outline_sections(
    claims: Iterable[ClaimDatum],
    references: List[str],
) -> List[Section]:
    ordered = _sorted_claims(claims)
    top_claim = ordered[0] if ordered else None

    abstract_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="要旨: ")] if top_claim else [_fallback_paragraph("要旨を記述してください。")]
    )
    background_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="背景: ")] if top_claim else [_fallback_paragraph("背景を記述してください。")]
    )
    objectives_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="目的: ")] if top_claim else [_fallback_paragraph("目的を記述してください。")]
    )
    methods_paragraphs = [
        _fallback_paragraph("[[YOUR_DATA_HERE]] 実験条件・図番号・統計を記述"),
        _fallback_paragraph("[[FIGURE_PLACEHOLDER]] 図の挿入位置を記述"),
        _fallback_paragraph("[[LAB_TERMS_CHECK]] ラボ用語整合の確認"),
    ]

    results_paragraphs: List[str] = []
    for idx, claim in enumerate(ordered[:5], start=1):
        results_paragraphs.append(_paragraph_from_claim(claim, prefix=f"結果{idx}: "))
    if not results_paragraphs:
        results_paragraphs.append(_fallback_paragraph("結果を記述してください。"))

    discussion_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="考察: ")] if top_claim else [_fallback_paragraph("考察を記述してください。")]
    )
    conclusion_paragraphs = (
        [_paragraph_from_claim(top_claim, prefix="結論: ")] if top_claim else [_fallback_paragraph("結論を記述してください。")]
    )

    reference_paragraphs = [f"- {ref}" for ref in references] or ["- [[REFERENCES_PLACEHOLDER]]"]

    return [
        Section("要旨 (Abstract)", abstract_paragraphs),
        Section("背景 (Background)", background_paragraphs),
        Section("目的 (Objectives)", objectives_paragraphs),
        Section("方法 (Methods)", methods_paragraphs),
        Section("結果 (Results)", results_paragraphs),
        Section("考察 (Discussion)", discussion_paragraphs),
        Section("結論 (Conclusion)", conclusion_paragraphs),
        Section("参考文献 (References)", reference_paragraphs),
    ]


def build_thesis_draft_sections(
    claims: Iterable[ClaimDatum],
    references: List[str],
) -> List[Section]:
    sections = build_thesis_outline_sections(claims, references)
    expanded_sections: List[Section] = []
    for section in sections:
        if section.title.startswith("結果"):
            expanded_sections.append(section)
            continue
        expanded_sections.append(section)
    return expanded_sections
