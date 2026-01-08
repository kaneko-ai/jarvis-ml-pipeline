"""Draft generation for research plan, thesis, and slides."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..export.docx_builder import build_docx_from_markdown
from ..export.pptx_builder import build_pptx_from_slides
from .citation_formatter import EvidenceLocator
from .outline_builder import (
    ClaimDatum,
    Section,
    build_research_plan_sections,
    build_thesis_draft_sections,
    build_thesis_outline_sections,
)
from .utils import load_overview

TEMPLATE_VERSION = "p5-v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _normalize_evidence(item: dict[str, Any]) -> EvidenceLocator:
    return EvidenceLocator(
        paper_id=str(item.get("paper_id") or item.get("paper") or "unknown"),
        chunk_id=str(item.get("chunk_id") or item.get("chunk") or "unknown"),
        section=str(item.get("section") or item.get("section_title") or "unknown"),
        paragraph=str(item.get("paragraph") or item.get("paragraph_id") or "unknown"),
        sentence=str(item.get("sentence") or item.get("sentence_id") or "unknown"),
        weak=bool(item.get("weak_evidence") or item.get("weak") or False),
    )


def _extract_evidence(raw: Any) -> list[EvidenceLocator]:
    if not raw:
        return []
    evidence_items: list[EvidenceLocator] = []
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict):
                evidence_items.append(_normalize_evidence(entry))
            else:
                evidence_items.append(
                    EvidenceLocator(
                        paper_id="unknown",
                        chunk_id=str(entry),
                        section="unknown",
                        paragraph="unknown",
                        sentence="unknown",
                        weak=False,
                    )
                )
    elif isinstance(raw, dict):
        evidence_items.append(_normalize_evidence(raw))
    else:
        evidence_items.append(
            EvidenceLocator(
                paper_id="unknown",
                chunk_id=str(raw),
                section="unknown",
                paragraph="unknown",
                sentence="unknown",
                weak=False,
            )
        )
    return evidence_items


def load_claims(run_dir: Path) -> list[ClaimDatum]:
    claims_dir = run_dir / "claims"
    claim_files = sorted(claims_dir.glob("*.claims.jsonl")) if claims_dir.exists() else []
    claims: list[ClaimDatum] = []

    for path in claim_files:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                text = data.get("claim") or data.get("text") or data.get("statement") or ""
                if not text:
                    continue
                evidence_raw = (
                    data.get("evidence") or data.get("citations") or data.get("citation_details")
                )
                evidence = _extract_evidence(evidence_raw)
                weak = bool(data.get("weak_evidence") or data.get("weak"))
                score = data.get("score") or data.get("rank_score")
                claims.append(
                    ClaimDatum(
                        text=text,
                        evidence=evidence,
                        weak=weak,
                        score=float(score) if score is not None else None,
                        claim_id=data.get("claim_id") or data.get("id"),
                    )
                )
    return claims


def _load_references(run_dir: Path, claims: Iterable[ClaimDatum]) -> list[str]:
    research_rank_path = run_dir / "research_rank.json"
    references: list[str] = []
    if research_rank_path.exists():
        try:
            data = _safe_read_json(research_rank_path)
            items = data.get("papers") or data.get("ranked") or data.get("items") or []
            for item in items:
                if isinstance(item, dict):
                    paper_id = item.get("paper_id") or item.get("id") or "unknown"
                    title = item.get("title") or ""
                    references.append(f"{paper_id}: {title}" if title else str(paper_id))
        except Exception:
            references = []

    if not references:
        paper_ids = {ev.paper_id for claim in claims for ev in claim.evidence if ev.paper_id}
        references = sorted(paper_ids) if paper_ids else []
    return references


def _sections_to_markdown(sections: Iterable[Section]) -> str:
    lines: list[str] = []
    for section in sections:
        lines.append(f"## {section.title}")
        lines.append("")
        for paragraph in section.paragraphs:
            if paragraph.startswith("- "):
                lines.append(paragraph)
            else:
                lines.append(paragraph)
                lines.append("")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_metadata_header(run_id: str) -> str:
    return f"Generated from run_id={run_id}, template_version={TEMPLATE_VERSION}, generated_at={_now()}\n\n"


def generate_markdown_research_plan(run_dir: Path, claims: list[ClaimDatum]) -> str:
    overview_text = load_overview(run_dir)
    references = _load_references(run_dir, claims)
    sections = build_research_plan_sections(claims, overview_text, references)
    return (
        "# Research Plan Draft\n\n"
        + _build_metadata_header(run_dir.name)
        + _sections_to_markdown(sections)
    )


def generate_markdown_thesis_outline(run_dir: Path, claims: list[ClaimDatum]) -> str:
    references = _load_references(run_dir, claims)
    sections = build_thesis_outline_sections(claims, references)
    return (
        "# Thesis Outline\n\n"
        + _build_metadata_header(run_dir.name)
        + _sections_to_markdown(sections)
    )


def generate_markdown_thesis_draft(run_dir: Path, claims: list[ClaimDatum]) -> str:
    references = _load_references(run_dir, claims)
    sections = build_thesis_draft_sections(claims, references)
    return (
        "# Thesis Draft\n\n"
        + _build_metadata_header(run_dir.name)
        + _sections_to_markdown(sections)
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_readme(run_dir: Path) -> None:
    writing_dir = run_dir / "writing"
    readme_path = writing_dir / "README.md"
    content = (
        "# Writing Outputs\n\n"
        "This folder contains auto-generated drafts for the research plan, thesis, and slides.\n"
        "- Markdown files are editable drafts with evidence locators appended per paragraph.\n"
        "- DOCX files are generated from the Markdown drafts for word processing.\n"
        "- PPTX file is a slide draft with placeholders for figures and lab-specific details.\n\n"
        f"Generated from run_id={run_dir.name}, template_version={TEMPLATE_VERSION}, generated_at={_now()}\n"
    )
    _write_text(readme_path, content)


def _update_manifest(run_dir: Path, outputs: list[str]) -> None:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = _safe_read_json(manifest_path)
    manifest["writing_template_version"] = TEMPLATE_VERSION
    manifest["writing_generated_at"] = _now()
    manifest["writing_outputs"] = outputs
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def generate_writing_outputs(run_id: str, outputs: dict[str, bool]) -> dict[str, Any]:
    run_dir = Path("data/runs") / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    claims = load_claims(run_dir)
    writing_dir = run_dir / "writing"
    writing_dir.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []

    if outputs.get("research_plan"):
        research_md = generate_markdown_research_plan(run_dir, claims)
        research_md_path = writing_dir / "research_plan_draft.md"
        _write_text(research_md_path, research_md)
        generated.append(str(research_md_path.relative_to(run_dir)))

        if outputs.get("docx"):
            docx_path = writing_dir / "research_plan_draft.docx"
            build_docx_from_markdown(research_md, docx_path)
            generated.append(str(docx_path.relative_to(run_dir)))

    if outputs.get("thesis"):
        outline_md = generate_markdown_thesis_outline(run_dir, claims)
        outline_path = writing_dir / "thesis_outline.md"
        _write_text(outline_path, outline_md)
        generated.append(str(outline_path.relative_to(run_dir)))

        thesis_md = generate_markdown_thesis_draft(run_dir, claims)
        thesis_path = writing_dir / "thesis_draft.md"
        _write_text(thesis_path, thesis_md)
        generated.append(str(thesis_path.relative_to(run_dir)))

        if outputs.get("docx"):
            thesis_docx_path = writing_dir / "thesis_draft.docx"
            build_docx_from_markdown(thesis_md, thesis_docx_path)
            generated.append(str(thesis_docx_path.relative_to(run_dir)))

    if outputs.get("slides") and outputs.get("pptx"):
        slides_path = writing_dir / "slides_draft.pptx"
        build_pptx_from_slides(run_dir, claims, slides_path)
        generated.append(str(slides_path.relative_to(run_dir)))

    _write_readme(run_dir)
    generated.append("writing/README.md")

    _update_manifest(run_dir, generated)

    return {"run_id": run_id, "outputs": generated, "template_version": TEMPLATE_VERSION}
