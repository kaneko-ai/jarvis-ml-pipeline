"""
JARVIS Pretrain Citation Reconstruction Stages

系統A: 引用再構成パイプライン
- 論文Aの背景・考察を、Aを見ずに引用集合R(A)から再構成
- citation-conditioned reasoning の評価データ生成
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jarvis_core.contracts.types import Artifacts, Claim, EvidenceLink, TaskContext
from jarvis_core.ops import log_audit
from jarvis_core.pipelines.stage_registry import register_stage

logger = logging.getLogger(__name__)

# ============================================
# データスキーマ
# ============================================


@dataclass
class ReferenceItem:
    """参照文献アイテム."""

    ref_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    journal: str = ""
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    raw: str = ""
    span_start: int = 0
    span_end: int = 0


@dataclass
class RDigestItem:
    """R_digest（入力圧縮）アイテム."""

    ref_id: str
    meta: dict[str, Any]
    abstract_digest: str
    key_findings: list[str]
    provenance: list[dict[str, Any]]


@dataclass
class ReconstructionOutput:
    """生成物（reconstruction）."""

    version: str = "1"
    background_points: list[dict[str, Any]] = field(default_factory=list)
    controversies: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    predicted_conclusions: list[dict[str, Any]] = field(default_factory=list)
    missing_critical_views: list[dict[str, Any]] = field(default_factory=list)
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass
class GoldPoint:
    """ゴールド要点."""

    point_id: str
    claim: str
    point_type: str  # background, controversy, hypothesis, conclusion, limitation
    span_start: int
    span_end: int


@dataclass
class MatchScore:
    """マッチスコア."""

    coverage: float = 0.0
    faithfulness: float = 0.0
    novelty_gap: float = 0.0
    structure: float = 0.0
    leakage_penalty: float = 0.0
    total: float = 0.0
    reasoning: str = ""


# ============================================
# 系統A: 引用再構成ステージ群
# ============================================


@register_stage("retrieval.get_paper_A", "論文A取得")
def stage_get_paper_A(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    論文Aを取得.

    入力: PMIDまたはURL（OAを優先）
    出力: artifacts.paper_A
    """
    # 入力からPMIDを取得
    pmid = context.constraints.get("pmid_a") or artifacts.metadata.get("pmid_a")

    if not pmid:
        # 最初のpapersからpaper_Aを設定
        if artifacts.papers:
            paper_a = artifacts.papers[0]
            artifacts.metadata["paper_A"] = paper_a.to_dict()
            artifacts.metadata["paper_A_pmid"] = paper_a.pmid
        else:
            artifacts.metadata["paper_A"] = None
            artifacts.metadata["paper_A_error"] = "No PMID provided"
    else:
        # PubMedから取得
        try:
            from jarvis_core.connectors.pubmed import get_pubmed_connector

            connector = get_pubmed_connector()
            papers = connector.fetch_details([pmid])

            if papers:
                paper = papers[0]
                artifacts.add_paper(paper.to_paper())
                artifacts.metadata["paper_A"] = {
                    "pmid": paper.pmid,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "sections": paper.sections,
                }
                artifacts.metadata["paper_A_pmid"] = paper.pmid
            else:
                artifacts.metadata["paper_A"] = None
                artifacts.metadata["paper_A_error"] = f"Paper not found: {pmid}"

        except Exception as e:
            artifacts.metadata["paper_A"] = None
            artifacts.metadata["paper_A_error"] = str(e)

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Paper A retrieved: {artifacts.metadata.get('paper_A_pmid', 'unknown')}",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="get_paper_A",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("retrieval.get_paper_A", "completed")
    return artifacts


@register_stage("extraction.references_from_A", "参照文献抽出")
def stage_references_from_A(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    論文Aから参照文献リストを抽出.

    出力: artifacts.references_R
    """
    paper_A = artifacts.metadata.get("paper_A", {})
    references = []

    # paper_Aのsectionsからreferencesを抽出
    if paper_A and "sections" in paper_A:
        ref_section = paper_A.get("sections", {}).get("References", "")

        # 簡易パース（実際にはより高度なパースが必要）
        import re

        # 番号付き参照のパターン
        ref_pattern = re.compile(r"(\d+)\.\s+(.+?)(?=\d+\.|$)", re.DOTALL)
        matches = ref_pattern.findall(ref_section)

        for i, (num, ref_text) in enumerate(matches):
            references.append(
                {
                    "ref_id": f"R{i+1}",
                    "raw": ref_text.strip()[:500],
                    "span_start": ref_section.find(ref_text),
                    "span_end": ref_section.find(ref_text) + len(ref_text),
                }
            )

    # フォールバック: 既存の参照がなければダミー
    if not references:
        references = [
            {"ref_id": f"R{i+1}", "raw": f"Reference {i+1}", "span_start": 0, "span_end": 10}
            for i in range(5)
        ]

    artifacts.metadata["references_R"] = references

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Extracted {len(references)} references from paper A",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="references_from_A",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("extraction.references_from_A", "completed", details={"ref_count": len(references)})
    return artifacts


@register_stage("retrieval.fetch_R_set", "R集合取得")
def stage_fetch_R_set(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    参照文献の詳細（要旨または本文）を取得.

    出力: artifacts.R_set_docs
    """
    references = artifacts.metadata.get("references_R", [])
    R_set_docs = []

    # 実際にはPMIDを解決して取得
    # ここではシンプルな実装
    for ref in references:
        R_set_docs.append(
            {
                "ref_id": ref.get("ref_id"),
                "title": ref.get("raw", "")[:100],
                "abstract": f"Abstract for {ref.get('ref_id')}",
                "status": "mock",  # available, unavailable
                "source": "mock",
            }
        )

    artifacts.metadata["R_set_docs"] = R_set_docs

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Fetched {len(R_set_docs)} R-set documents",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="fetch_R_set",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("retrieval.fetch_R_set", "completed", details={"docs_count": len(R_set_docs)})
    return artifacts


@register_stage("screening.leakage_filter", "リーク検出フィルタ")
def stage_leakage_filter(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    答え漏洩の検出.

    R(A)内にAの結論・表現がそのままあると、再構成タスクが「要約ゲーム」になる。

    重要: ここでAの背景/考察本文を使うと漏洩するので禁止。
    """
    paper_A = artifacts.metadata.get("paper_A", {})
    R_set_docs = artifacts.metadata.get("R_set_docs", [])

    # Aのタイトル・アブスト要約からキーフレーズを抽出
    paper_A.get("title", "").lower()
    a_abstract = paper_A.get("abstract", "")[:500].lower()

    # 簡易リーク検出
    leakage_flags = []
    R_set_filtered = []

    for doc in R_set_docs:
        doc_abstract = doc.get("abstract", "").lower()

        # 類似度計算（簡易: キーワード一致率）
        a_words = set(a_abstract.split())
        doc_words = set(doc_abstract.split())

        if a_words and doc_words:
            overlap = len(a_words & doc_words) / len(a_words)
        else:
            overlap = 0.0

        # リーク判定
        if overlap > 0.5:
            leakage_level = "high"
        elif overlap > 0.3:
            leakage_level = "medium"
        else:
            leakage_level = "low"

        leakage_flags.append(
            {"ref_id": doc.get("ref_id"), "leakage_level": leakage_level, "overlap_score": overlap}
        )

        # フィルタリング（high以外は通す）
        if leakage_level != "high":
            R_set_filtered.append(doc)

    artifacts.metadata["leakage_flags"] = leakage_flags
    artifacts.metadata["R_set_filtered"] = R_set_filtered

    high_leakage_count = sum(1 for f in leakage_flags if f["leakage_level"] == "high")

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Leakage filter: {high_leakage_count} high-leakage docs removed",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="leakage_filter",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("screening.leakage_filter", "completed", details={"high_leakage": high_leakage_count})
    return artifacts


@register_stage("summarization.R_set_digest", "R集合ダイジェスト")
def stage_R_set_digest(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    R集合を入力圧縮.

    各文献のdigestは必ずprovenance（title/abstract/span）を保持。
    """
    R_set_filtered = artifacts.metadata.get("R_set_filtered", [])

    R_digest = {"digest_version": "1", "refs": []}

    for doc in R_set_filtered:
        digest_item = {
            "ref_id": doc.get("ref_id"),
            "meta": {
                "title": doc.get("title", ""),
                "study_type": "other",  # clinical, animal, cell, review, other
            },
            "abstract_digest": doc.get("abstract", "")[:200],
            "key_findings": [],
            "provenance": [
                {
                    "doc_id": doc.get("ref_id"),
                    "chunk_id": "abstract",
                    "start": 0,
                    "end": min(200, len(doc.get("abstract", ""))),
                }
            ],
        }
        R_digest["refs"].append(digest_item)

    artifacts.metadata["R_digest"] = R_digest

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"R-set digest created: {len(R_digest['refs'])} refs",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="R_set_digest",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("summarization.R_set_digest", "completed")
    return artifacts


@register_stage("generation.reconstruct_background_discussion", "背景・考察再構成")
def stage_reconstruct_background_discussion(
    context: TaskContext, artifacts: Artifacts
) -> Artifacts:
    """
    R_digestから背景・考察を再構成.

    重要: paper_A本文は絶対に使わない。
    """
    artifacts.metadata.get("R_digest", {})

    # 再構成出力（実際にはLLMで生成）
    reconstruction = {
        "reconstruction_version": "1",
        "background_points": [
            {
                "text": "Background point from R-set analysis",
                "evidence": [{"ref_id": "R1", "chunk_id": "abstract", "start": 0, "end": 50}],
            }
        ],
        "controversies": [],
        "hypotheses": [
            {
                "text": "Hypothesized mechanism based on R-set",
                "test": "Experimental validation needed",
                "evidence": [],
            }
        ],
        "predicted_conclusions": [{"text": "Predicted conclusion", "prob": 0.65, "evidence": []}],
        "missing_critical_views": [],
        "notes": {"uncertainties": ["Limited R-set coverage"]},
    }

    artifacts.metadata["reconstruction"] = reconstruction

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Background/discussion reconstructed from R-set",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="reconstruct",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("generation.reconstruct_background_discussion", "completed")
    return artifacts


@register_stage("extraction.gold_from_A", "ゴールド要点抽出")
def stage_gold_from_A(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    論文Aから教師信号（ゴールド要点）を抽出.

    対象セクション: Introduction, Discussion
    """
    paper_A = artifacts.metadata.get("paper_A", {})

    gold_points = []

    # Introduction/Backgroundから
    intro_text = paper_A.get("sections", {}).get(
        "Introduction", paper_A.get("sections", {}).get("Background", "")
    )

    if intro_text:
        gold_points.append(
            {
                "point_id": "g1",
                "claim": intro_text[:200],
                "point_type": "background",
                "span_start": 0,
                "span_end": min(200, len(intro_text)),
            }
        )

    # Discussion/Conclusionから
    disc_text = paper_A.get("sections", {}).get(
        "Discussion", paper_A.get("sections", {}).get("Conclusion", "")
    )

    if disc_text:
        gold_points.append(
            {
                "point_id": "g2",
                "claim": disc_text[:200],
                "point_type": "conclusion",
                "span_start": 0,
                "span_end": min(200, len(disc_text)),
            }
        )

    artifacts.metadata["gold_points"] = gold_points

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Extracted {len(gold_points)} gold points from paper A",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="gold_from_A",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("extraction.gold_from_A", "completed", details={"gold_count": len(gold_points)})
    return artifacts


@register_stage("evaluation.match_score", "マッチスコア計算")
def stage_match_score(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    reconstructionとgold_pointsのマッチスコアを計算.

    スコア設計:
    - Coverage: ゴールド要点のカバー率
    - Faithfulness: R由来根拠スパン整合
    - Novelty/Gap: Aが触れていない妥当な欠落指摘
    - Structure: 因果/仮説/争点の接続
    - Leakage penalty: 漏洩が強いほど減点
    """
    reconstruction = artifacts.metadata.get("reconstruction", {})
    gold_points = artifacts.metadata.get("gold_points", [])
    leakage_flags = artifacts.metadata.get("leakage_flags", [])

    # スコア計算（簡易）
    bg_count = len(reconstruction.get("background_points", []))
    gold_count = len(gold_points)

    coverage = min(1.0, bg_count / max(1, gold_count))

    # Faithfulness: evidence付きの割合
    points_with_evidence = sum(
        1 for p in reconstruction.get("background_points", []) if p.get("evidence")
    )
    faithfulness = points_with_evidence / max(1, bg_count) if bg_count > 0 else 0.0

    # Novelty
    novelty_gap = len(reconstruction.get("missing_critical_views", [])) * 0.1

    # Structure
    structure = 0.5 if reconstruction.get("hypotheses") else 0.0

    # Leakage penalty
    high_leakage_ratio = sum(1 for f in leakage_flags if f.get("leakage_level") == "high") / max(
        1, len(leakage_flags)
    )
    leakage_penalty = high_leakage_ratio * 0.3

    # Total
    total = (
        coverage * 0.3 + faithfulness * 0.3 + novelty_gap * 0.1 + structure * 0.2
    ) - leakage_penalty
    total = max(0.0, min(1.0, total))

    match_score = {
        "coverage": coverage,
        "faithfulness": faithfulness,
        "novelty_gap": novelty_gap,
        "structure": structure,
        "leakage_penalty": leakage_penalty,
        "total": total,
        "reasoning": f"Coverage={coverage:.2f}, Faithfulness={faithfulness:.2f}",
    }

    artifacts.metadata["match_score"] = match_score

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Match score calculated: {total:.2f}",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="match_score",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("evaluation.match_score", "completed", details={"total_score": total})
    return artifacts


@register_stage("quality_gate.no_leakage", "リーク禁止ゲート")
def stage_no_leakage_gate(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    高リーク文献が一定割合を超えたrunは学習データとして保存禁止.

    ただし「監査用」としては保存して良い（別フォルダへ）。
    """
    leakage_flags = artifacts.metadata.get("leakage_flags", [])

    high_leakage_count = sum(1 for f in leakage_flags if f.get("leakage_level") == "high")
    total_count = len(leakage_flags)

    high_leakage_ratio = high_leakage_count / max(1, total_count)
    max_allowed_ratio = 0.3  # 30%以上はNG

    passed = high_leakage_ratio <= max_allowed_ratio

    artifacts.metadata["no_leakage_gate"] = {
        "passed": passed,
        "high_leakage_ratio": high_leakage_ratio,
        "threshold": max_allowed_ratio,
        "save_to_training": passed,
        "save_to_audit": True,  # 常に監査用は保存
    }

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"No-leakage gate: {'PASSED' if passed else 'FAILED'} ({high_leakage_ratio:.1%})",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="no_leakage",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit(
        "quality_gate.no_leakage",
        "completed",
        details={"passed": passed, "ratio": high_leakage_ratio},
    )
    return artifacts


@register_stage("ops.store_training_record", "学習レコード保存")
def stage_store_training_record(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    JSONL 1行（学習レコード）を保存.

    datasets/pretrain/citation_reconstruction.jsonl に追記
    追記は run_id で重複排除（hashで管理）
    """
    gate_result = artifacts.metadata.get("no_leakage_gate", {})

    if not gate_result.get("save_to_training", False):
        artifacts.metadata["training_record_saved"] = False
        artifacts.metadata["training_record_reason"] = "Leakage gate failed"
    else:
        # レコード作成
        paper_A = artifacts.metadata.get("paper_A", {})
        R_digest = artifacts.metadata.get("R_digest", {})
        reconstruction = artifacts.metadata.get("reconstruction", {})
        gold_points = artifacts.metadata.get("gold_points", [])
        match_score = artifacts.metadata.get("match_score", {})
        leakage_flags = artifacts.metadata.get("leakage_flags", [])

        # record_hash
        hash_input = f"{paper_A.get('pmid', '')}_{json.dumps(R_digest, sort_keys=True)}_v1"
        record_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        record = {
            "run_id": context.run_id,
            "record_hash": record_hash,
            "paper_A_id": paper_A.get("pmid", ""),
            "R_digest_hash": hashlib.sha256(
                json.dumps(R_digest, sort_keys=True).encode()
            ).hexdigest()[:16],
            "reconstruction": reconstruction,
            "gold_points": gold_points,
            "scores": match_score,
            "leakage_flags": leakage_flags,
            "provenance": {},
            "created_at": datetime.now().isoformat(),
        }

        # 保存
        output_dir = Path("datasets/pretrain")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "citation_reconstruction.jsonl"

        try:
            # 重複チェック
            existing_hashes = set()
            if output_path.exists():
                with open(output_path, encoding="utf-8") as f:
                    for line in f:
                        try:
                            existing = json.loads(line)
                            existing_hashes.add(existing.get("record_hash", ""))
                        except Exception as e:
                            logger.debug(f"Failed to parse line in {output_path}: {e}")

            if record_hash not in existing_hashes:
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                artifacts.metadata["training_record_saved"] = True
                artifacts.metadata["training_record_path"] = str(output_path)
            else:
                artifacts.metadata["training_record_saved"] = False
                artifacts.metadata["training_record_reason"] = "Duplicate record"

        except Exception as e:
            artifacts.metadata["training_record_saved"] = False
            artifacts.metadata["training_record_error"] = str(e)

    saved = artifacts.metadata.get("training_record_saved", False)

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Training record: {'saved' if saved else 'skipped'}",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="store_training",
                    chunk_id="log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("ops.store_training_record", "completed", details={"saved": saved})
    return artifacts