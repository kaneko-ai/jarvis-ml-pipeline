"""Phase Λ: Extended Analysis Modules (Λ-1 to Λ-30).

Per Research OS v3.0 specification.
All 30 functions in one file for maintainability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# =========================
# Λ-1〜Λ-5: 仮説・主張系
# =========================


def analyze_hypothesis_risks(hypothesis: str, vectors: list[PaperVector]) -> dict:
    """Λ-1: 仮説リスク分解."""
    risks = []
    if not vectors:
        risks.append("裏付けデータなし")
    if len(hypothesis) > 200:
        risks.append("仮説が複雑すぎる")
    return {"hypothesis": hypothesis[:50], "risks": risks, "risk_count": len(risks)}


def score_concept_competition(c1: str, c2: str, vectors: list[PaperVector]) -> dict:
    """Λ-2: Concept競合度スコア."""
    c1_count = sum(1 for v in vectors if c1 in v.concept.concepts)
    c2_count = sum(1 for v in vectors if c2 in v.concept.concepts)
    overlap = sum(1 for v in vectors if c1 in v.concept.concepts and c2 in v.concept.concepts)
    competition = overlap / max(c1_count + c2_count - overlap, 1)
    return {"concepts": [c1, c2], "competition_score": round(competition, 2)}


def detect_theme_overlap(themes: list[str], vectors: list[PaperVector]) -> list[dict]:
    """Λ-3: テーマ被り検出."""
    overlaps = []
    for i, t1 in enumerate(themes):
        for t2 in themes[i + 1 :]:
            overlaps.append({"themes": [t1, t2], "overlap": "potential"})
    return overlaps[:5]


def detect_claim_ambiguity(claim: str) -> dict:
    """Λ-4: 主張曖昧度検出."""
    ambiguous_words = ["may", "might", "possibly", "おそらく", "かもしれない"]
    found = [w for w in ambiguous_words if w in claim.lower()]
    return {"claim": claim[:50], "ambiguity_score": len(found) / 5, "found_words": found}


def warn_strong_assumptions(hypothesis: str) -> list[str]:
    """Λ-5: 強すぎる前提警告."""
    strong_words = ["必ず", "絶対", "always", "definitely", "proves"]
    warnings = [w for w in strong_words if w in hypothesis.lower()]
    return warnings if warnings else ["警告なし"]


# =========================
# Λ-6〜Λ-10: 実験設計系
# =========================


def build_experiment_dependency_graph(experiments: list[str]) -> dict:
    """Λ-6: 実験依存グラフ."""
    nodes = [{"id": i, "name": e[:30]} for i, e in enumerate(experiments)]
    edges = [{"from": i, "to": i + 1} for i in range(len(experiments) - 1)]
    return {"nodes": nodes, "edges": edges}


def detect_experiment_bottleneck(experiments: list[str], durations: list[int]) -> dict:
    """Λ-7: 実験ボトルネック検出."""
    if not experiments or not durations:
        return {"bottleneck": None}
    max_idx = durations.index(max(durations))
    return {"bottleneck": experiments[max_idx], "duration": durations[max_idx]}


def warn_control_shortage(methods: list[str]) -> list[str]:
    """Λ-8: コントロール不足警告."""
    needed = []
    if "knockout" in str(methods).lower():
        needed.append("wild-type control")
    if "drug" in str(methods).lower():
        needed.append("vehicle control")
    return needed if needed else ["コントロール十分"]


def optimize_experiment_order(experiments: list[str], costs: list[float]) -> list[str]:
    """Λ-9: 実験順序最適化."""
    if not experiments:
        return []
    paired = list(zip(experiments, costs))
    paired.sort(key=lambda x: x[1])
    return [p[0] for p in paired]


def detect_reproduction_failure_signs(vectors: list[PaperVector]) -> list[str]:
    """Λ-10: 再現失敗兆候検出."""
    signs = []
    if vectors:
        methods = set()
        for v in vectors:
            methods.update(v.method.methods.keys())
        if len(methods) < 2:
            signs.append("手法の多様性不足")
    return signs if signs else ["兆候なし"]


# =========================
# Λ-11〜Λ-15: 論文補助系
# =========================


def detect_reviewer_fatigue_points(text: str) -> list[str]:
    """Λ-11: Reviewer疲労ポイント."""
    points = []
    if len(text) > 10000:
        points.append("本文が長すぎる")
    if text.count(".") > 100:
        points.append("文が多すぎる")
    return points if points else ["問題なし"]


def warn_misleading_expressions(text: str) -> list[str]:
    """Λ-12: 誤解表現警告."""
    misleading = ["clearly shows", "undoubtedly", "明らかに", "確実に"]
    found = [m for m in misleading if m in text]
    return found if found else []


def check_figure_claim_consistency(figures: list[str], claims: list[str]) -> dict:
    """Λ-13: Figure-Claim整合性."""
    coverage = min(len(figures), len(claims)) / max(len(claims), 1)
    return {"consistency_score": round(coverage, 2), "figures": len(figures), "claims": len(claims)}


def warn_supplement_bloat(supplement_pages: int) -> str:
    """Λ-14: Supplement肥大警告."""
    if supplement_pages > 50:
        return "Supplementが肥大（50ページ超）"
    elif supplement_pages > 30:
        return "Supplement要確認"
    return "適切"


def evaluate_citation_balance(vectors: list[PaperVector]) -> dict:
    """Λ-15: 引用バランス評価."""
    if not vectors:
        return {"balance": "unknown"}
    years = [v.metadata.year for v in vectors if v.metadata.year]
    if not years:
        return {"balance": "unknown"}
    recent = sum(1 for y in years if y >= 2020)
    ratio = recent / len(years)
    return {"recent_ratio": round(ratio, 2), "balance": "good" if 0.3 < ratio < 0.7 else "skewed"}


# =========================
# Λ-16〜Λ-20: トレンド分析系
# =========================


def detect_rising_concepts(vectors: list[PaperVector]) -> list[str]:
    """Λ-16: 急上昇Concept検出."""
    recent_concepts = set()
    for v in vectors:
        if (v.metadata.year or 0) >= 2022:
            recent_concepts.update(v.concept.concepts.keys())
    return list(recent_concepts)[:10]


def predict_technique_lifespan(technique: str, vectors: list[PaperVector]) -> dict:
    """Λ-17: 技術流行寿命予測."""
    count = sum(1 for v in vectors if technique in v.method.methods)
    lifespan = min(10, 3 + count)
    return {"technique": technique, "predicted_lifespan_years": lifespan, "estimated": True}


def detect_emerging_journals(vectors: list[PaperVector]) -> list[str]:
    """Λ-18: 新興ジャーナル検出."""
    journals = {}
    for v in vectors:
        j = v.metadata.journal or "unknown"
        year = v.metadata.year or 0
        if year >= 2020:
            journals[j] = journals.get(j, 0) + 1
    return [j for j, c in journals.items() if c >= 2][:5]


def cluster_researchers(vectors: list[PaperVector]) -> dict:
    """Λ-19: 研究者クラスタ分析."""
    # Simplified: cluster by concept
    clusters = {}
    for v in vectors:
        for c in list(v.concept.concepts.keys())[:1]:
            if c not in clusters:
                clusters[c] = []
            clusters[c].append(v.paper_id)
    return {"clusters": clusters}


def detect_cross_field_citations(vectors: list[PaperVector]) -> int:
    """Λ-20: 分野横断引用検出."""
    # Count unique concept combinations
    pairs = set()
    for v in vectors:
        concepts = list(v.concept.concepts.keys())
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1 :]:
                pairs.add((c1, c2))
    return len(pairs)


# =========================
# Λ-21〜Λ-25: 自己分析系
# =========================


def classify_hypothesis_type(hypothesis: str) -> str:
    """Λ-21: 仮説タイプ自己分析."""
    if "mechanism" in hypothesis.lower() or "mechanism" in hypothesis:
        return "mechanistic"
    elif "correlation" in hypothesis.lower():
        return "correlational"
    return "exploratory"


def classify_thinking_style(vectors: list[PaperVector]) -> str:
    """Λ-22: 思考型分類."""
    if not vectors:
        return "unknown"
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    if avg_novelty > 0.7:
        return "innovator"
    elif avg_novelty > 0.4:
        return "developer"
    return "consolidator"


def diagnose_research_speed(papers_per_year: float) -> str:
    """Λ-23: 研究スピード診断."""
    if papers_per_year > 5:
        return "high_output"
    elif papers_per_year > 2:
        return "moderate"
    return "methodical"


def alert_decision_delay(months_since_last_decision: int) -> str:
    """Λ-24: 決断遅延アラート."""
    if months_since_last_decision > 6:
        return "critical: 決断が6ヶ月以上遅延"
    elif months_since_last_decision > 3:
        return "warning: 決断を検討すべき時期"
    return "ok"


def detect_undervaluation(vectors: list[PaperVector]) -> bool:
    """Λ-25: 成果過小評価検出."""
    if not vectors:
        return False
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)
    return avg_novelty > avg_impact + 0.2


# =========================
# Λ-26〜Λ-30: 運用・継続系
# =========================


def restructure_for_obsidian(vectors: list[PaperVector]) -> dict:
    """Λ-26: Obsidian知識再構成."""
    nodes = []
    for v in vectors:
        nodes.append(
            {
                "id": v.paper_id,
                "links": list(v.concept.concepts.keys())[:3],
            }
        )
    return {"obsidian_nodes": nodes, "total": len(nodes)}


def optimize_for_notebooklm(vectors: list[PaperVector]) -> dict:
    """Λ-27: NotebookLM音声最適化."""
    summaries = []
    for v in vectors[:5]:
        concepts = list(v.concept.concepts.keys())[:2]
        summaries.append(f"{v.paper_id}: {', '.join(concepts)}")
    return {"audio_summaries": summaries}


def generate_monthly_inventory(vectors: list[PaperVector]) -> dict:
    """Λ-28: 月次研究棚卸し."""
    return {
        "total_papers": len(vectors),
        "concepts": len(set(c for v in vectors for c in v.concept.concepts)),
        "methods": len(set(m for v in vectors for m in v.method.methods)),
        "status": "complete",
    }


def suggest_log_improvements(log_entries: int) -> list[str]:
    """Λ-29: 研究ログ自己改善."""
    suggestions = []
    if log_entries < 10:
        suggestions.append("ログ記録の頻度向上を推奨")
    if log_entries < 5:
        suggestions.append("日次記録の習慣化")
    return suggestions if suggestions else ["ログ運用良好"]


def generate_monthly_strategy_brief(vectors: list[PaperVector]) -> str:
    """Λ-30: 月次研究戦略ブリーフ."""
    if not vectors:
        return "データ蓄積中"

    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    direction = "攻め（新規テーマ開拓）" if avg_novelty > 0.6 else "守り（既存テーマ深掘り）"
    return f"今月の戦略: {direction}。論文数: {len(vectors)}"
