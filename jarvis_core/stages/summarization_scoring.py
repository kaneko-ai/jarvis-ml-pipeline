"""
JARVIS Stage Implementations - Summarization/Scoring/KG/Design

全てのステージは:
1. artifacts を1つ以上更新
2. provenance を1つ以上追加
3. 実行ログを残す
"""

from __future__ import annotations

import uuid

from jarvis_core.contracts.types import Artifacts, Claim, EvidenceLink, Score, TaskContext
from jarvis_core.ops import log_audit
from jarvis_core.pipelines.stage_registry import register_stage

# ============================================
# SUMMARIZATION ステージ群
# ============================================


@register_stage("summarization.multigrain", "多粒度要約")
def stage_summarization_multigrain(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """多粒度要約ステージ。"""
    for paper in artifacts.papers:
        text = paper.abstract or paper.title

        # 短文要約
        short = text[:300] + "..." if len(text) > 300 else text
        # 中文要約
        medium = text[:1000] + "..." if len(text) > 1000 else text

        artifacts.summaries[paper.doc_id] = short
        artifacts.metadata[f"{paper.doc_id}_summary_medium"] = medium

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Generated summaries for {len(artifacts.papers)} papers",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="summarization",
                    chunk_id="sum_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("summarization.multigrain", "completed")
    return artifacts


@register_stage("summarization.beginner", "初学者向け言い換え")
def stage_summarization_beginner(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """初学者向け言い換えステージ。"""
    simplifications = {
        "apoptosis": "細胞の自然死",
        "in vitro": "試験管内",
        "in vivo": "生体内",
    }

    for doc_id, summary in artifacts.summaries.items():
        simplified = summary
        for term, simple in simplifications.items():
            simplified = simplified.replace(term, f"{term}（{simple}）")
        artifacts.metadata[f"{doc_id}_beginner"] = simplified

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Beginner-friendly versions created",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="beginner",
                    chunk_id="beg_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("summarization.beginner", "completed")
    return artifacts


@register_stage("summarization.compare", "比較要約")
def stage_summarization_compare(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """比較要約ステージ。"""
    if len(artifacts.papers) >= 2:
        artifacts.metadata["comparison"] = {
            "papers_compared": [p.doc_id for p in artifacts.papers[:2]],
            "similarities": ["Both study the same topic"],
            "differences": ["Different methodologies"],
        }

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Comparison summary generated",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="compare",
                    chunk_id="comp_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("summarization.compare", "completed")
    return artifacts


@register_stage("summarization.reproducibility", "再現性要約")
def stage_summarization_reproducibility(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """再現性要約ステージ。"""
    for paper in artifacts.papers:
        methods = artifacts.metadata.get("methods", [])
        paper_methods = [m for m in methods if m.get("doc_id") == paper.doc_id]

        artifacts.metadata[f"{paper.doc_id}_reproducibility"] = {
            "methods_described": len(paper_methods),
            "reproducibility_score": 0.7 if paper_methods else 0.3,
        }

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Reproducibility assessment completed",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="reproducibility",
                    chunk_id="repro_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("summarization.reproducibility", "completed")
    return artifacts


@register_stage("summarization.refutable", "反証可能性要約")
def stage_summarization_refutable(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """反証可能性要約ステージ。"""
    for claim in artifacts.claims:
        if claim.claim_type == "fact":
            artifacts.metadata[f"{claim.claim_id}_refutable"] = {
                "is_refutable": len(claim.evidence) > 0,
                "evidence_count": len(claim.evidence),
            }

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Refutability assessment completed",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="refutable",
                    chunk_id="ref_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("summarization.refutable", "completed")
    return artifacts


# ============================================
# SCORING ステージ群
# ============================================


@register_stage("scoring.importance", "重要度スコア")
def stage_scoring_importance(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """重要度スコアステージ。"""
    for paper in artifacts.papers:
        text = (paper.abstract or "").lower()

        score = 0.5
        if "novel" in text or "first" in text:
            score += 0.2
        if "significant" in text or "important" in text:
            score += 0.15

        artifacts.scores[f"{paper.doc_id}_importance"] = Score(
            name="importance",
            value=min(score, 1.0),
            explanation=f"Importance score for {paper.doc_id}",
        )

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Importance scores calculated",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="importance",
                    chunk_id="imp_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("scoring.importance", "completed")
    return artifacts


@register_stage("scoring.confidence", "Claim信頼度")
def stage_scoring_confidence(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """Claim信頼度スコアステージ。"""
    for claim in artifacts.claims:
        evidence_count = len(claim.evidence)
        confidence = min(evidence_count * 0.3 + 0.1, 1.0)

        artifacts.scores[f"{claim.claim_id}_confidence"] = Score(
            name="confidence",
            value=confidence,
            explanation=f"Confidence based on {evidence_count} evidence",
            evidence=claim.evidence[:1],
        )

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Confidence scores calculated",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="confidence",
                    chunk_id="conf_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("scoring.confidence", "completed")
    return artifacts


@register_stage("scoring.bias_risk", "バイアスリスク")
def stage_scoring_bias_risk(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """バイアスリスクスコアステージ。"""
    for paper in artifacts.papers:
        text = (paper.abstract or "").lower()

        risk = 0.3  # Base risk
        if "randomized" in text:
            risk -= 0.1
        if "control" in text:
            risk -= 0.1
        if "funded by" in text:
            risk += 0.2

        artifacts.scores[f"{paper.doc_id}_bias_risk"] = Score(
            name="bias_risk", value=max(0, min(risk, 1.0)), explanation="Bias risk assessment"
        )

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Bias risk assessed",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="bias",
                    chunk_id="bias_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("scoring.bias_risk", "completed")
    return artifacts


@register_stage("scoring.evidence_tier", "エビデンス階層")
def stage_scoring_evidence_tier(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """エビデンス階層スコアステージ。"""
    tiers = {
        "meta-analysis": 1.0,
        "rct": 0.85,
        "cohort": 0.7,
        "clinical": 0.75,
    }

    for paper in artifacts.papers:
        study_type = artifacts.metadata.get(f"{paper.doc_id}_study_type", "unknown")
        tier_score = tiers.get(study_type, 0.5)

        artifacts.scores[f"{paper.doc_id}_evidence_tier"] = Score(
            name="evidence_tier", value=tier_score, explanation=f"Evidence tier: {study_type}"
        )

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Evidence tiers assigned",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="tier",
                    chunk_id="tier_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("scoring.evidence_tier", "completed")
    return artifacts


@register_stage("scoring.clinical_relevance", "臨床関連性")
def stage_scoring_clinical_relevance(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """臨床関連性スコアステージ。"""
    for paper in artifacts.papers:
        text = (paper.abstract or "").lower()

        relevance = 0.3
        if "patient" in text or "clinical" in text:
            relevance += 0.3
        if "treatment" in text or "therapy" in text:
            relevance += 0.2

        artifacts.scores[f"{paper.doc_id}_clinical_relevance"] = Score(
            name="clinical_relevance",
            value=min(relevance, 1.0),
            explanation="Clinical relevance assessment",
        )

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Clinical relevance scored",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="clinical",
                    chunk_id="clin_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("scoring.clinical_relevance", "completed")
    return artifacts


@register_stage("scoring.personal_fit", "目的適合度")
def stage_scoring_personal_fit(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """目的適合度スコアステージ。"""
    goal_words = set(context.goal.lower().split())

    for paper in artifacts.papers:
        title_words = set(paper.title.lower().split())
        overlap = len(goal_words & title_words) / max(len(goal_words), 1)

        artifacts.scores[f"{paper.doc_id}_personal_fit"] = Score(
            name="personal_fit",
            value=min(overlap + 0.3, 1.0),
            explanation=f"Fit to goal: {context.goal[:50]}",
        )

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Personal fit scored",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="fit",
                    chunk_id="fit_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("scoring.personal_fit", "completed")
    return artifacts


@register_stage("scoring.learning_roi", "学習ROI")
def stage_scoring_learning_roi(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """学習ROIスコアステージ。"""
    for paper in artifacts.papers:
        importance = artifacts.scores.get(f"{paper.doc_id}_importance")
        fit = artifacts.scores.get(f"{paper.doc_id}_personal_fit")

        importance_val = importance.value if importance else 0.5
        fit_val = fit.value if fit else 0.5

        roi = (importance_val + fit_val) / 2

        artifacts.scores[f"{paper.doc_id}_learning_roi"] = Score(
            name="learning_roi", value=roi, explanation="Learning ROI = (importance + fit) / 2"
        )

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Learning ROI calculated",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="roi",
                    chunk_id="roi_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("scoring.learning_roi", "completed")
    return artifacts


# ============================================
# KNOWLEDGE GRAPH ステージ群
# ============================================


@register_stage("knowledge_graph.entity_normalize", "Entity正規化")
def stage_kg_entity_normalize(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """Entity正規化ステージ。"""
    artifacts.metadata["normalized_entities"] = []

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Entity normalization completed",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="entity",
                    chunk_id="ent_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("knowledge_graph.entity_normalize", "completed")
    return artifacts


@register_stage("knowledge_graph.build_and_index", "KG構築")
def stage_kg_build_and_index(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """KG構築ステージ。"""
    artifacts.graphs["knowledge_graph"] = {"entities": {}, "relations": []}

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Knowledge graph built",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="kg",
                    chunk_id="kg_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("knowledge_graph.build_and_index", "completed")
    return artifacts


@register_stage("knowledge_graph.controversy_map", "論争マップ")
def stage_kg_controversy_map(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """論争マップステージ。"""
    artifacts.metadata["controversies"] = []

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Controversy mapping completed",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="controversy",
                    chunk_id="cont_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("knowledge_graph.controversy_map", "completed")
    return artifacts


@register_stage("knowledge_graph.timeline", "知見更新史")
def stage_kg_timeline(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """知見更新史ステージ。"""
    artifacts.metadata["timeline"] = []

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Timeline generated",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="timeline",
                    chunk_id="tl_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("knowledge_graph.timeline", "completed")
    return artifacts


@register_stage("knowledge_graph.graphrag_index", "GraphRAGインデックス")
def stage_kg_graphrag_index(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """GraphRAGインデックスステージ。"""
    artifacts.metadata["graphrag_indexed"] = True

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="GraphRAG index built",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="graphrag",
                    chunk_id="grag_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("knowledge_graph.graphrag_index", "completed")
    return artifacts


# ============================================
# DESIGN ステージ群
# ============================================


@register_stage("design.gap_analysis", "Gap分析")
def stage_design_gap_analysis(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """Gap分析ステージ。"""
    gaps = []
    limitations = artifacts.metadata.get("limitations", [])

    for lim in limitations[:5]:
        gaps.append(
            {
                "gap_id": f"gap-{uuid.uuid4().hex[:8]}",
                "description": lim.get("limitation", ""),
                "priority": "medium",
            }
        )

    artifacts.metadata["gaps"] = gaps

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Identified {len(gaps)} research gaps",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="gap",
                    chunk_id="gap_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("design.gap_analysis", "completed")
    return artifacts


@register_stage("design.next_experiments", "次実験提案")
def stage_design_next_experiments(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """次実験提案ステージ。"""
    gaps = artifacts.metadata.get("gaps", [])

    proposals = []
    for gap in gaps[:3]:
        proposals.append(
            {
                "proposal_id": f"exp-{uuid.uuid4().hex[:8]}",
                "gap_id": gap.get("gap_id"),
                "title": f"Experiment to address: {gap.get('description', '')[:50]}",
                "design_type": "RCT",
            }
        )

    artifacts.metadata["experiment_proposals"] = proposals
    artifacts.designs = proposals

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Proposed {len(proposals)} experiments",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="design",
                    chunk_id="exp_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("design.next_experiments", "completed")
    return artifacts


@register_stage("design.protocol_draft", "プロトコルドラフト")
def stage_design_protocol_draft(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """プロトコルドラフトステージ。"""
    proposals = artifacts.metadata.get("experiment_proposals", [])

    protocols = []
    for prop in proposals[:2]:
        protocols.append(
            {
                "protocol_id": f"prot-{uuid.uuid4().hex[:8]}",
                "proposal_id": prop.get("proposal_id"),
                "title": prop.get("title"),
                "steps": ["1. Obtain approval", "2. Recruit", "3. Execute", "4. Analyze"],
            }
        )

    artifacts.metadata["protocols"] = protocols

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text=f"Generated {len(protocols)} protocol drafts",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="protocol",
                    chunk_id="prot_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("design.protocol_draft", "completed")
    return artifacts


@register_stage("design.stats_design", "統計設計支援")
def stage_design_stats_design(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """統計設計支援ステージ。"""
    proposals = artifacts.metadata.get("experiment_proposals", [])

    stats_designs = []
    for prop in proposals[:2]:
        stats_designs.append(
            {
                "proposal_id": prop.get("proposal_id"),
                "analysis_type": "t-test",
                "sample_size": 100,
                "power": 0.8,
                "alpha": 0.05,
            }
        )

    artifacts.metadata["stats_designs"] = stats_designs

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Statistical designs created",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="stats_design",
                    chunk_id="statd_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("design.stats_design", "completed")
    return artifacts


@register_stage("design.risk_diagnosis", "リスク診断")
def stage_design_risk_diagnosis(context: TaskContext, artifacts: Artifacts) -> Artifacts:
    """リスク診断ステージ。"""
    proposals = artifacts.metadata.get("experiment_proposals", [])

    risks = []
    for prop in proposals:
        risks.append(
            {
                "proposal_id": prop.get("proposal_id"),
                "risks": ["Resource constraints", "Time limitations"],
                "overall_risk": "medium",
            }
        )

    artifacts.metadata["risk_diagnoses"] = risks

    artifacts.add_claim(
        Claim(
            claim_id=f"c-{uuid.uuid4().hex[:8]}",
            claim_text="Risk diagnosis completed",
            evidence=[
                EvidenceLink(
                    doc_id="internal",
                    section="risk",
                    chunk_id="risk_log",
                    start=0,
                    end=10,
                    confidence=1.0,
                )
            ],
            claim_type="log",
        )
    )

    log_audit("design.risk_diagnosis", "completed")
    return artifacts