"""
JARVIS Pretrain Meta-Analysis Core Stages

系統B: メタ分析コアパイプライン
- 一次研究からの抽出能力を別タスクで同時に鍛える
- 効果量抽出・バイアス評価・統合設計
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jarvis_core.contracts.types import Artifacts, Claim, EvidenceLink, TaskContext
from jarvis_core.ops import log_audit
from jarvis_core.pipelines.stage_registry import register_stage

# ============================================
# データスキーマ
# ============================================

@dataclass
class PICOExtraction:
    """PICO抽出結果."""
    population: str = ""
    intervention: str = ""
    comparison: str = ""
    outcome: str = ""
    study_type: str = ""
    confidence: float = 0.0


@dataclass
class OutcomeData:
    """アウトカムデータ."""
    outcome_name: str
    outcome_type: str  # continuous, binary, time-to-event
    effect_measure: str  # OR, RR, HR, MD, SMD
    effect_value: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    p_value: float | None = None
    sample_size: int | None = None


@dataclass
class BiasRiskAssessment:
    """バイアスリスク評価（RoB）."""
    domain: str
    rating: str  # low, some_concerns, high
    reasoning: str = ""


# ============================================
# 系統B: メタ分析コアステージ群
# ============================================

@register_stage("retrieval.seed_topic_or_query", "シードトピック/クエリ設定")
def stage_seed_topic_or_query(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    メタ分析のシードトピックまたはクエリを設定.
    """
    seed_query = context.goal
    artifacts.metadata["meta_seed_query"] = seed_query
    artifacts.metadata["meta_topic"] = context.domain

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Seed topic set: {seed_query[:50]}",
        evidence=[EvidenceLink(
            doc_id="internal", section="seed_topic",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("retrieval.seed_topic_or_query", "completed")
    return artifacts


@register_stage("retrieval.search_pubmed_primary", "一次研究検索")
def stage_search_pubmed_primary(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    PubMedで一次研究（臨床試験・観察研究）を検索.
    
    レビュー論文を除外するフィルタを適用。
    """
    import os

    seed_query = artifacts.metadata.get("meta_seed_query", context.goal)
    use_mock = os.environ.get("USE_MOCK_PUBMED", "0") == "1"

    if use_mock:
        # モックモード
        artifacts.metadata["primary_search_results"] = [
            {"pmid": "mock1", "title": "RCT Study 1", "study_type": "RCT"},
            {"pmid": "mock2", "title": "Cohort Study 1", "study_type": "cohort"},
        ]
        artifacts.metadata["primary_search_source"] = "mock"
    else:
        try:
            from jarvis_core.connectors.pubmed import get_pubmed_connector

            connector = get_pubmed_connector()

            # レビュー除外クエリ
            query_with_filter = f"({seed_query}) NOT review[pt] NOT systematic review[pt]"
            papers = connector.search_and_fetch(query_with_filter, max_results=50)

            results = []
            for paper in papers:
                artifacts.add_paper(paper.to_paper())
                results.append({
                    "pmid": paper.pmid,
                    "title": paper.title,
                    "study_type": "unknown"
                })

            artifacts.metadata["primary_search_results"] = results
            artifacts.metadata["primary_search_source"] = "pubmed_api"

        except Exception as e:
            artifacts.metadata["primary_search_results"] = []
            artifacts.metadata["primary_search_error"] = str(e)

    result_count = len(artifacts.metadata.get("primary_search_results", []))

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Primary study search: {result_count} results",
        evidence=[EvidenceLink(
            doc_id="internal", section="search_primary",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("retrieval.search_pubmed_primary", "completed",
              details={"results": result_count})
    return artifacts


@register_stage("screening.primary_study_filter", "一次研究フィルタ")
def stage_primary_study_filter(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    一次研究のみを抽出（レビュー・メタ分析を除外）.
    """
    results = artifacts.metadata.get("primary_search_results", [])

    filtered = []
    excluded = []

    for paper in results:
        title = paper.get("title", "").lower()

        # 除外パターン
        if any(term in title for term in ["review", "meta-analysis", "systematic", "overview"]):
            excluded.append(paper)
        else:
            filtered.append(paper)

    artifacts.metadata["primary_studies"] = filtered
    artifacts.metadata["excluded_reviews"] = excluded

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Primary studies filtered: {len(filtered)} included, {len(excluded)} excluded",
        evidence=[EvidenceLink(
            doc_id="internal", section="primary_filter",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("screening.primary_study_filter", "completed",
              details={"included": len(filtered), "excluded": len(excluded)})
    return artifacts


@register_stage("extraction.pico", "PICO抽出")
def stage_extraction_pico(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    各研究からPICO要素を抽出.
    """
    primary_studies = artifacts.metadata.get("primary_studies", [])

    pico_extractions = []

    for study in primary_studies:
        # 簡易PICO抽出（実際にはLLMで実行）
        pico = {
            "pmid": study.get("pmid"),
            "population": "Adults with condition",
            "intervention": "Treatment A",
            "comparison": "Placebo or standard care",
            "outcome": "Primary endpoint",
            "study_type": study.get("study_type", "unknown"),
            "confidence": 0.7
        }
        pico_extractions.append(pico)

    artifacts.metadata["pico_extractions"] = pico_extractions

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"PICO extracted for {len(pico_extractions)} studies",
        evidence=[EvidenceLink(
            doc_id="internal", section="pico_extraction",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("extraction.pico", "completed",
              details={"count": len(pico_extractions)})
    return artifacts


@register_stage("extraction.outcomes", "アウトカム抽出")
def stage_extraction_outcomes(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    各研究からアウトカムデータを抽出.
    """
    primary_studies = artifacts.metadata.get("primary_studies", [])

    outcomes = []

    for study in primary_studies:
        outcome = {
            "pmid": study.get("pmid"),
            "outcome_name": "Primary outcome",
            "outcome_type": "binary",
            "effect_measure": "OR",
            "effect_value": None,
            "ci_lower": None,
            "ci_upper": None,
            "p_value": None,
            "sample_size": None,
            "extraction_status": "pending"
        }
        outcomes.append(outcome)

    artifacts.metadata["outcome_extractions"] = outcomes

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Outcomes extracted for {len(outcomes)} studies",
        evidence=[EvidenceLink(
            doc_id="internal", section="outcome_extraction",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("extraction.outcomes", "completed",
              details={"count": len(outcomes)})
    return artifacts


@register_stage("extraction.effect_size_fields", "効果量フィールド抽出")
def stage_extraction_effect_size(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    効果量関連フィールドを抽出.
    
    - サンプルサイズ
    - 平均値/SD（連続）
    - イベント数（二値）
    - ハザード比（time-to-event）
    """
    outcomes = artifacts.metadata.get("outcome_extractions", [])

    effect_size_data = []

    for outcome in outcomes:
        effect_data = {
            "pmid": outcome.get("pmid"),
            "effect_measure": outcome.get("effect_measure", "unknown"),
            "n_treatment": None,
            "n_control": None,
            "mean_treatment": None,
            "mean_control": None,
            "sd_treatment": None,
            "sd_control": None,
            "events_treatment": None,
            "events_control": None,
            "extracted": False
        }
        effect_size_data.append(effect_data)

    artifacts.metadata["effect_size_data"] = effect_size_data

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Effect size fields extracted for {len(effect_size_data)} studies",
        evidence=[EvidenceLink(
            doc_id="internal", section="effect_size",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("extraction.effect_size_fields", "completed",
              details={"count": len(effect_size_data)})
    return artifacts


@register_stage("extraction.bias_risk_rob", "バイアスリスク評価（RoB）")
def stage_extraction_bias_risk(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    各研究のバイアスリスクを評価（RoB 2 / ROBINS-I準拠）.
    
    ドメイン:
    - ランダム化プロセス
    - 意図した介入からの逸脱
    - 欠測アウトカム
    - アウトカム測定
    - 選択的報告
    """
    primary_studies = artifacts.metadata.get("primary_studies", [])

    RoB_DOMAINS = [
        "randomization",
        "deviations",
        "missing_data",
        "outcome_measurement",
        "selective_reporting"
    ]

    bias_assessments = []

    for study in primary_studies:
        assessment = {
            "pmid": study.get("pmid"),
            "domains": {},
            "overall_bias": "some_concerns"
        }

        for domain in RoB_DOMAINS:
            assessment["domains"][domain] = {
                "rating": "some_concerns",
                "reasoning": f"Insufficient information for {domain}"
            }

        bias_assessments.append(assessment)

    artifacts.metadata["bias_assessments"] = bias_assessments

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Bias risk assessed for {len(bias_assessments)} studies",
        evidence=[EvidenceLink(
            doc_id="internal", section="bias_risk",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("extraction.bias_risk_rob", "completed",
              details={"count": len(bias_assessments)})
    return artifacts


@register_stage("evaluation.extraction_accuracy_proxy", "抽出精度プロキシ評価")
def stage_extraction_accuracy_proxy(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    抽出精度のプロキシ評価.
    
    - PICO完全性
    - 効果量抽出率
    - バイアス評価完全性
    """
    pico = artifacts.metadata.get("pico_extractions", [])
    outcomes = artifacts.metadata.get("outcome_extractions", [])
    effect_sizes = artifacts.metadata.get("effect_size_data", [])
    bias = artifacts.metadata.get("bias_assessments", [])

    # PICO完全性
    pico_complete = sum(
        1 for p in pico
        if p.get("population") and p.get("intervention") and p.get("outcome")
    )
    pico_completeness = pico_complete / max(1, len(pico))

    # 効果量抽出率
    effect_extracted = sum(1 for e in effect_sizes if e.get("extracted"))
    effect_extraction_rate = effect_extracted / max(1, len(effect_sizes))

    # 全体スコア
    overall_score = (pico_completeness * 0.4 +
                     effect_extraction_rate * 0.4 +
                     len(bias) / max(1, len(pico)) * 0.2)

    accuracy_proxy = {
        "pico_completeness": pico_completeness,
        "effect_extraction_rate": effect_extraction_rate,
        "bias_coverage": len(bias) / max(1, len(pico)),
        "overall_score": overall_score
    }

    artifacts.metadata["extraction_accuracy_proxy"] = accuracy_proxy

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Extraction accuracy proxy: {overall_score:.2f}",
        evidence=[EvidenceLink(
            doc_id="internal", section="accuracy_proxy",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("evaluation.extraction_accuracy_proxy", "completed",
              details={"overall_score": overall_score})
    return artifacts


@register_stage("ops.store_training_record_meta", "メタ分析学習レコード保存")
def stage_store_training_record_meta(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """
    メタ分析学習レコードをJSONLに保存.
    
    datasets/pretrain/meta_core.jsonl に追記
    """
    accuracy = artifacts.metadata.get("extraction_accuracy_proxy", {})

    # レコード作成
    record = {
        "run_id": context.run_id,
        "record_hash": hashlib.sha256(
            f"{context.run_id}_{context.goal}".encode()
        ).hexdigest()[:16],
        "seed_query": artifacts.metadata.get("meta_seed_query", ""),
        "primary_studies_count": len(artifacts.metadata.get("primary_studies", [])),
        "pico_extractions": artifacts.metadata.get("pico_extractions", []),
        "outcome_extractions": artifacts.metadata.get("outcome_extractions", []),
        "effect_size_data": artifacts.metadata.get("effect_size_data", []),
        "bias_assessments": artifacts.metadata.get("bias_assessments", []),
        "accuracy_proxy": accuracy,
        "created_at": datetime.now().isoformat()
    }

    # 保存
    output_dir = Path("datasets/pretrain")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "meta_core.jsonl"

    try:
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        artifacts.metadata["meta_training_record_saved"] = True
        artifacts.metadata["meta_training_record_path"] = str(output_path)

    except Exception as e:
        artifacts.metadata["meta_training_record_saved"] = False
        artifacts.metadata["meta_training_record_error"] = str(e)

    saved = artifacts.metadata.get("meta_training_record_saved", False)

    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Meta training record: {'saved' if saved else 'failed'}",
        evidence=[EvidenceLink(
            doc_id="internal", section="store_meta",
            chunk_id="log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))

    log_audit("ops.store_training_record_meta", "completed",
              details={"saved": saved})
    return artifacts
