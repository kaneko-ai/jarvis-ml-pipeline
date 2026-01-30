"""
JARVIS MVP Pipeline

Phase B: 一本道MVP - 論文検索→根拠抽出→Bundle出力

入力: query, constraints
出力: runs/<run_id>/bundle (papers, claims, evidence, scores, report)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# Input Schema
# ============================================================


@dataclass
class Constraints:
    """検索制約."""

    oa_only: bool = True
    max_papers: int = 10
    date_from: str | None = None
    date_to: str | None = None
    domain: list[str] = field(default_factory=list)


@dataclass
class Reproducibility:
    """再現性情報."""

    seed: int = 0
    model: str = "local"
    pipeline_version: str = "mvp-v1"


@dataclass
class PipelineInput:
    """パイプライン入力."""

    goal: str
    query: str
    constraints: Constraints = field(default_factory=Constraints)
    reproducibility: Reproducibility = field(default_factory=Reproducibility)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "query": self.query,
            "constraints": asdict(self.constraints),
            "reproducibility": asdict(self.reproducibility),
        }

    def save(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


# ============================================================
# Output Schema
# ============================================================


@dataclass
class Paper:
    """論文メタデータ."""

    paper_id: str
    title: str
    authors: list[str]
    year: int
    abstract: str
    source: str  # pubmed, arxiv, etc
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Claim:
    """主張."""

    paper_id: str
    claim_id: str
    claim: str
    claim_type: str  # result, method, background, interpretation
    confidence: str  # low, med, high

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceLocator:
    """根拠の位置."""

    section: str
    paragraph: int
    sentence: int
    offset_start: int
    offset_end: int


@dataclass
class Evidence:
    """根拠."""

    paper_id: str
    claim_id: str
    source: str  # abstract, fulltext
    locator: EvidenceLocator
    evidence_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "claim_id": self.claim_id,
            "source": self.source,
            "locator": asdict(self.locator),
            "evidence_text": self.evidence_text,
        }


@dataclass
class Warning:
    """警告."""

    type: str  # no_evidence, fetch_failed, etc
    message: str
    paper_id: str | None = None
    claim_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Scores:
    """スコア."""

    papers: dict[str, dict[str, float]] = field(default_factory=dict)

    def add_paper_score(self, paper_id: str, features: dict[str, float]) -> None:
        self.papers[paper_id] = features

    def to_dict(self) -> dict[str, Any]:
        return {"papers": self.papers}


# ============================================================
# Bundle
# ============================================================


@dataclass
class Bundle:
    """出力バンドル."""

    run_id: str
    input: PipelineInput
    papers: list[Paper] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    scores: Scores = field(default_factory=Scores)
    warnings: list[Warning] = field(default_factory=list)

    def save(self, output_dir: Path) -> Path:
        """バンドルを保存."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # input.json
        self.input.save(output_dir / "input.json")

        # papers.jsonl
        with open(output_dir / "papers.jsonl", "w", encoding="utf-8") as f:
            for p in self.papers:
                f.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")

        # claims.jsonl
        with open(output_dir / "claims.jsonl", "w", encoding="utf-8") as f:
            for c in self.claims:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")

        # evidence.jsonl
        with open(output_dir / "evidence.jsonl", "w", encoding="utf-8") as f:
            for e in self.evidence:
                f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")

        # scores.json
        with open(output_dir / "scores.json", "w", encoding="utf-8") as f:
            json.dump(self.scores.to_dict(), f, indent=2, ensure_ascii=False)

        # warnings.jsonl
        with open(output_dir / "warnings.jsonl", "w", encoding="utf-8") as f:
            for w in self.warnings:
                f.write(json.dumps(w.to_dict(), ensure_ascii=False) + "\n")

        # report.md
        self._generate_report(output_dir / "report.md")

        logger.info(f"Bundle saved: {output_dir}")
        return output_dir

    def _generate_report(self, path: Path) -> None:
        """レポートを生成."""
        lines = [
            f"# Research Report: {self.input.goal}",
            "",
            f"**Run ID**: {self.run_id}",
            f"**Query**: {self.input.query}",
            f"**Generated**: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"- Papers: {len(self.papers)}",
            f"- Claims: {len(self.claims)}",
            f"- Evidence: {len(self.evidence)}",
            f"- Warnings: {len(self.warnings)}",
            "",
        ]

        # 論文一覧
        if self.papers:
            lines.append("## Papers")
            for i, p in enumerate(self.papers[:5], 1):
                lines.append(f"### {i}. {p.title}")
                lines.append(f"- **Authors**: {', '.join(p.authors[:3])}")
                lines.append(f"- **Year**: {p.year}")
                lines.append(f"- **Source**: {p.source}")
                lines.append("")

        # Top claims with evidence
        if self.claims:
            lines.append("## Key Claims")
            claim_evidence = {c.claim_id: [] for c in self.claims}
            for e in self.evidence:
                if e.claim_id in claim_evidence:
                    claim_evidence[e.claim_id].append(e)

            for c in self.claims[:5]:
                evs = claim_evidence.get(c.claim_id, [])
                lines.append(f"- **{c.claim}** [{c.confidence}]")
                if evs:
                    lines.append(f'  - Evidence: "{evs[0].evidence_text[:100]}..."')
                else:
                    lines.append("  - ⚠️ No evidence found")
                lines.append("")

        # Warnings
        if self.warnings:
            lines.append("## Warnings")
            for w in self.warnings:
                lines.append(f"- [{w.type}] {w.message}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


# ============================================================
# MVP Pipeline
# ============================================================


class MVPPipeline:
    """MVP一本道パイプライン.

    Phase B: cheap→expensive二段構え
    1. Retrieve metadata (cheap)
    2. Cheap summarize (abstract中心)
    3. Select candidates (top_k)
    4. Extract claims/evidence (expensive)
    5. Bundle export
    """

    def __init__(self, runs_dir: str = "runs"):
        """初期化."""
        self.runs_dir = Path(runs_dir)

    def run(self, input: PipelineInput) -> Bundle:
        """パイプラインを実行."""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.runs_dir / run_id

        logger.info("=== MVP Pipeline Start ===")
        logger.info(f"Run ID: {run_id}")
        logger.info(f"Goal: {input.goal}")
        logger.info(f"Query: {input.query}")

        bundle = Bundle(run_id=run_id, input=input)

        # Stage 1: Retrieve metadata (cheap)
        papers = self._retrieve_papers(input)
        bundle.papers = papers

        if not papers:
            bundle.warnings.append(
                Warning(
                    type="no_papers",
                    message=f"No papers found for query: {input.query}",
                )
            )
            bundle.save(output_dir)
            return bundle

        # Stage 2: Cheap summarize (abstract中心)
        # → この段階では abstract のみ使用

        # Stage 3: Select candidates (top_k)
        top_k = min(3, len(papers))  # expensive passは上位3本まで
        candidates = papers[:top_k]
        logger.info(f"Selected {top_k} candidates for expensive pass")

        # Stage 4: Extract claims/evidence (expensive)
        for paper in candidates:
            claims, evidence, warnings = self._extract_claims_evidence(paper)
            bundle.claims.extend(claims)
            bundle.evidence.extend(evidence)
            bundle.warnings.extend(warnings)

        # Stage 5: Scoring
        for paper in papers:
            bundle.scores.add_paper_score(
                paper.paper_id,
                {
                    "recency": self._score_recency(paper.year),
                    "evidence_count": len(
                        [e for e in bundle.evidence if e.paper_id == paper.paper_id]
                    ),
                },
            )

        # Save bundle
        bundle.save(output_dir)

        logger.info("=== MVP Pipeline Complete ===")
        logger.info(f"Papers: {len(bundle.papers)}")
        logger.info(f"Claims: {len(bundle.claims)}")
        logger.info(f"Evidence: {len(bundle.evidence)}")

        return bundle

    def _retrieve_papers(self, input: PipelineInput) -> list[Paper]:
        """論文を取得（デモ用のダミーデータ）."""
        # TODO: 実際のPubMed/arXiv APIに接続
        logger.info(f"Retrieving papers for: {input.query}")

        # デモ用ダミーデータ
        papers = []
        for i in range(min(input.constraints.max_papers, 5)):
            papers.append(
                Paper(
                    paper_id=f"PMID:{1000 + i}",
                    title=f"Study on {input.query} - Part {i+1}",
                    authors=["Author A", "Author B"],
                    year=2024 - i,
                    abstract=f"This study investigates {input.query}. We found significant results.",
                    source="pubmed",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{1000+i}",
                )
            )

        return papers

    def _extract_claims_evidence(self, paper: Paper) -> tuple:
        """主張と根拠を抽出."""
        claims = []
        evidence = []
        warnings = []

        # デモ用: abstractから1つのclaimを生成
        claim_id = f"{paper.paper_id}_c001"

        claim = Claim(
            paper_id=paper.paper_id,
            claim_id=claim_id,
            claim=f"Findings from {paper.title}",
            claim_type="result",
            confidence="med",
        )
        claims.append(claim)

        # 根拠を紐付け
        if paper.abstract:
            evidence.append(
                Evidence(
                    paper_id=paper.paper_id,
                    claim_id=claim_id,
                    source="abstract",
                    locator=EvidenceLocator(
                        section="Abstract",
                        paragraph=1,
                        sentence=1,
                        offset_start=0,
                        offset_end=len(paper.abstract),
                    ),
                    evidence_text=paper.abstract,
                )
            )
        else:
            warnings.append(
                Warning(
                    type="no_evidence",
                    message=f"No evidence found for claim {claim_id}",
                    paper_id=paper.paper_id,
                    claim_id=claim_id,
                )
            )

        return claims, evidence, warnings

    def _score_recency(self, year: int) -> float:
        """年度スコア."""
        current_year = 2024
        age = current_year - year
        return max(0.0, 1.0 - age * 0.1)