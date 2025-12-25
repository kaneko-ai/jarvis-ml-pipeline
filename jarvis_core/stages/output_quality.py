"""
JARVIS Stage Implementations - Output/Quality Gate/Render

全てのステージは:
1. artifacts を1つ以上更新
2. provenance を1つ以上追加
3. 実行ログを残す
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict

from jarvis_core.contracts.types import Artifacts, Claim, EvidenceLink, TaskContext
from jarvis_core.pipelines.stage_registry import register_stage
from jarvis_core.ops import log_audit


# ============================================
# OUTPUT ステージ群
# ============================================

@register_stage("output.render_dashboard", "ダッシュボード出力")
def stage_output_render_dashboard(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """ダッシュボード出力ステージ。"""
    dashboard = {
        "run_id": context.run_id,
        "goal": context.goal,
        "domain": context.domain,
        "papers_count": len(artifacts.papers),
        "claims_count": len(artifacts.claims),
        "scores_count": len(artifacts.scores),
        "widgets": []
    }
    
    # Summary widget
    if artifacts.summaries:
        dashboard["widgets"].append({
            "type": "text",
            "title": "概要",
            "data": list(artifacts.summaries.values())[:3]
        })
    
    # Scores widget
    if artifacts.scores:
        dashboard["widgets"].append({
            "type": "chart",
            "title": "スコア",
            "data": {k: v.value for k, v in list(artifacts.scores.items())[:10]}
        })
    
    artifacts.metadata["dashboard"] = dashboard
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text="Dashboard rendered",
        evidence=[EvidenceLink(
            doc_id="internal", section="dashboard",
            chunk_id="dash_log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("output.render_dashboard", "completed")
    return artifacts


@register_stage("output.evidence_highlight", "根拠ハイライト")
def stage_output_evidence_highlight(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """根拠ハイライトステージ。"""
    highlights = []
    
    for claim in artifacts.claims:
        if claim.evidence:
            for ev in claim.evidence:
                highlights.append({
                    "claim_id": claim.claim_id,
                    "doc_id": ev.doc_id,
                    "section": ev.section,
                    "start": ev.start,
                    "end": ev.end,
                    "text": ev.text[:100] if ev.text else ""
                })
    
    artifacts.metadata["evidence_highlights"] = highlights
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Generated {len(highlights)} evidence highlights",
        evidence=[EvidenceLink(
            doc_id="internal", section="highlight",
            chunk_id="hl_log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("output.evidence_highlight", "completed")
    return artifacts


@register_stage("output.score_bar", "スコアバー生成")
def stage_output_score_bar(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """スコアバー生成ステージ。"""
    score_bars = []
    
    for score_key, score in artifacts.scores.items():
        score_bars.append({
            "key": score_key,
            "value": score.value,
            "percentage": int(score.value * 100),
            "explanation": score.explanation
        })
    
    artifacts.metadata["score_bars"] = score_bars
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Generated {len(score_bars)} score bars",
        evidence=[EvidenceLink(
            doc_id="internal", section="score_bar",
            chunk_id="sb_log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("output.score_bar", "completed")
    return artifacts


@register_stage("output.comparison_view", "比較ビュー出力")
def stage_output_comparison_view(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """比較ビュー出力ステージ。"""
    comparison = artifacts.metadata.get("comparison", {})
    artifacts.metadata["comparison_view"] = {
        "enabled": bool(comparison),
        "data": comparison
    }
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text="Comparison view generated",
        evidence=[EvidenceLink(
            doc_id="internal", section="comparison_view",
            chunk_id="cv_log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("output.comparison_view", "completed")
    return artifacts


@register_stage("output.design_view", "実験設計ビュー出力")
def stage_output_design_view(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """実験設計ビュー出力ステージ。"""
    proposals = artifacts.metadata.get("experiment_proposals", [])
    protocols = artifacts.metadata.get("protocols", [])
    
    artifacts.metadata["design_view"] = {
        "proposals": proposals,
        "protocols": protocols,
        "total_proposals": len(proposals)
    }
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text="Design view generated",
        evidence=[EvidenceLink(
            doc_id="internal", section="design_view",
            chunk_id="dv_log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("output.design_view", "completed")
    return artifacts


@register_stage("output.export_bundle", "結果バンドル出力")
def stage_output_export_bundle(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """結果バンドル出力ステージ。"""
    bundle = {
        "run_id": context.run_id,
        "goal": context.goal,
        "domain": context.domain,
        "timestamp": context.timestamp,
        "papers": [
            {"doc_id": p.doc_id, "title": p.title}
            for p in artifacts.papers
        ],
        "claims_count": len(artifacts.claims),
        "scores": {k: v.value for k, v in artifacts.scores.items()},
        "summaries": dict(artifacts.summaries)
    }
    
    artifacts.metadata["export_bundle"] = bundle
    
    # ファイル出力（オプショナル）
    output_dir = Path("artifacts/bundles")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / f"bundle_{context.run_id}.json"
    
    try:
        with open(bundle_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # CI環境ではスキップ
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text="Export bundle created",
        evidence=[EvidenceLink(
            doc_id="internal", section="export",
            chunk_id="exp_log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("output.export_bundle", "completed")
    return artifacts


# ============================================
# QUALITY GATE ステージ
# ============================================

@register_stage("quality_gate.provenance_check", "根拠率チェック（≥95%）")
def stage_quality_gate_provenance_check(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """根拠率チェック（≥95%必須）。"""
    from jarvis_core.evaluation import get_quality_gates
    
    gates = get_quality_gates()
    result = gates.check_provenance(artifacts.claims)
    
    artifacts.metadata["provenance_check"] = {
        "passed": result.passed,
        "threshold": result.threshold,
        "actual": result.actual,
        "message": result.message
    }
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Provenance check: {result.actual:.1%} (threshold: {result.threshold:.1%})",
        evidence=[EvidenceLink(
            doc_id="internal", section="quality_gate",
            chunk_id="prov_check", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("quality_gate.provenance_check", "completed",
              details={"passed": result.passed, "rate": result.actual})
    return artifacts


@register_stage("quality_gate.final_audit", "最終監査")
def stage_quality_gate_final_audit(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """最終監査ステージ。"""
    from jarvis_core.ops import get_audit_logger
    
    logger = get_audit_logger()
    summary = logger.get_summary()
    
    artifacts.metadata["final_audit"] = {
        "run_id": summary.get("run_id"),
        "entries": summary.get("entries", 0),
        "errors": summary.get("errors", 0),
        "avg_provenance_rate": summary.get("avg_provenance_rate", 0)
    }
    
    artifacts.add_claim(Claim(
        claim_id=f"c-{uuid.uuid4().hex[:8]}",
        claim_text=f"Final audit: {summary.get('entries', 0)} entries, {summary.get('errors', 0)} errors",
        evidence=[EvidenceLink(
            doc_id="internal", section="final_audit",
            chunk_id="audit_log", start=0, end=10, confidence=1.0
        )],
        claim_type="log"
    ))
    
    log_audit("quality_gate.final_audit", "completed",
              provenance_rate=summary.get("avg_provenance_rate", 0))
    return artifacts
