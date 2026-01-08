"""Phase Σ: Extended Research Analysis Modules.

This file contains all 30 extended RP modules (Σ-1 to Σ-30).
Organized by category for maintainability.

思考・仮説系: Σ-1〜Σ-7
分析・可視化系: Σ-8〜Σ-13
実験・設計系: Σ-14〜Σ-19
論文・発表補助: Σ-20〜Σ-25
継続・運用系: Σ-26〜Σ-30
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# =========================
# Σ-1〜Σ-7: 思考・仮説系
# =========================

def score_hypothesis(hypothesis: str, vectors: list[PaperVector]) -> dict:
    """Σ-1: Score a hypothesis based on evidence."""
    if not hypothesis or not vectors:
        return {"score": 0.5, "estimated": True}

    related = sum(1 for v in vectors for c in v.concept.concepts if c.lower() in hypothesis.lower())
    score = min(1.0, related / max(len(vectors), 1))

    return {
        "hypothesis": hypothesis[:50],
        "score": round(score, 3),
        "evidence_count": related,
        "estimated": True,
    }


def analyze_hypothesis_dependencies(hypotheses: list[str], vectors: list[PaperVector]) -> list[dict]:
    """Σ-2: Analyze dependencies between hypotheses."""
    deps = []
    for i, h1 in enumerate(hypotheses):
        for j, h2 in enumerate(hypotheses):
            if i >= j:
                continue
            # Simple word overlap
            words1 = set(h1.lower().split())
            words2 = set(h2.lower().split())
            overlap = len(words1 & words2) / max(len(words1 | words2), 1)
            if overlap > 0.2:
                deps.append({"h1": i, "h2": j, "dependency": round(overlap, 2)})
    return deps


def generate_negative_hypothesis(hypothesis: str) -> str:
    """Σ-3: Generate negation of hypothesis."""
    if "is" in hypothesis.lower():
        return hypothesis.replace("is", "is not", 1)
    return f"It is NOT the case that {hypothesis}"


def estimate_hypothesis_lifetime(hypothesis: str, vectors: list[PaperVector]) -> dict:
    """Σ-4: Estimate how long a hypothesis will remain relevant."""
    if not vectors:
        return {"years_remaining": 5, "estimated": True}

    years = [v.metadata.year for v in vectors if v.metadata.year]
    if not years:
        return {"years_remaining": 5, "estimated": True}

    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    years_remaining = max(1, int(10 * avg_novelty))

    return {"years_remaining": years_remaining, "latest_year": max(years), "estimated": True}


def detect_consensus(vectors: list[PaperVector], concept: str) -> dict:
    """Σ-5: Detect consensus on a concept."""
    if not vectors:
        return {"consensus": False, "agreement": 0.0}

    relevant = [v for v in vectors for c in v.concept.concepts if concept.lower() in c.lower()]
    if len(relevant) < 2:
        return {"consensus": False, "agreement": 0.0, "sample_size": len(relevant)}

    # Check axis agreement
    axes = [v.biological_axis.immune_activation for v in relevant]
    variance = sum((x - sum(axes)/len(axes))**2 for x in axes) / len(axes)
    agreement = 1 / (1 + variance)

    return {"consensus": agreement > 0.7, "agreement": round(agreement, 2), "sample_size": len(relevant)}


def find_counter_evidence(hypothesis: str, vectors: list[PaperVector]) -> list[dict]:
    """Σ-6: Find counter-evidence for a hypothesis."""
    counters = []
    for v in vectors:
        # Simple heuristic: papers with opposite axis values
        if v.biological_axis.immune_activation < -0.3:
            counters.append({
                "paper_id": v.paper_id,
                "reason": "反対の免疫軸を示す",
            })
    return counters[:5]


def generate_hypothesis_diagram(hypotheses: list[str]) -> dict:
    """Σ-7: Generate hypothesis relationship diagram data."""
    nodes = [{"id": i, "label": h[:30]} for i, h in enumerate(hypotheses)]
    edges = []
    for i in range(len(hypotheses) - 1):
        edges.append({"from": i, "to": i + 1, "type": "sequence"})
    return {"nodes": nodes, "edges": edges}


# =========================
# Σ-8〜Σ-13: 分析・可視化系
# =========================

def build_impact_heatmap(vectors: list[PaperVector]) -> dict[str, dict[str, float]]:
    """Σ-8: Build impact heatmap by year and concept."""
    heatmap = {}
    for v in vectors:
        year = str(v.metadata.year) if v.metadata.year else "unknown"
        if year not in heatmap:
            heatmap[year] = {}
        for c in v.concept.concepts:
            heatmap[year][c] = heatmap[year].get(c, 0) + v.impact.future_potential
    return heatmap


def analyze_cluster_dynamics(vectors: list[PaperVector]) -> list[dict]:
    """Σ-9: Analyze cluster dynamics over time."""
    by_year = {}
    for v in vectors:
        year = v.metadata.year or 0
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(v)

    dynamics = []
    for year in sorted(by_year.keys()):
        papers = by_year[year]
        avg_axis = sum(v.biological_axis.immune_activation for v in papers) / len(papers)
        dynamics.append({"year": year, "avg_axis": round(avg_axis, 2), "count": len(papers)})
    return dynamics


def infer_causal_direction(c1: str, c2: str, vectors: list[PaperVector]) -> dict:
    """Σ-10: Infer causal direction between concepts."""
    c1_years = []
    c2_years = []
    for v in vectors:
        if c1 in v.concept.concepts:
            c1_years.append(v.metadata.year or 0)
        if c2 in v.concept.concepts:
            c2_years.append(v.metadata.year or 0)

    if not c1_years or not c2_years:
        return {"direction": "unknown", "estimated": True}

    avg_c1 = sum(c1_years) / len(c1_years)
    avg_c2 = sum(c2_years) / len(c2_years)

    if avg_c1 < avg_c2:
        return {"direction": f"{c1} → {c2}", "estimated": True}
    else:
        return {"direction": f"{c2} → {c1}", "estimated": True}


def map_method_failures(vectors: list[PaperVector]) -> dict[str, float]:
    """Σ-11: Map method failure rates (estimated)."""
    methods = {}
    for v in vectors:
        for m in v.method.methods:
            if m not in methods:
                methods[m] = []
            # Low impact = potential failure
            methods[m].append(v.impact.future_potential)

    failure_map = {}
    for m, impacts in methods.items():
        avg = sum(impacts) / len(impacts)
        failure_map[m] = round(1 - avg, 2)  # Lower impact = higher failure
    return failure_map


def map_journal_trends(vectors: list[PaperVector]) -> dict[str, int]:
    """Σ-12: Map journal publication trends."""
    journals = {}
    for v in vectors:
        j = v.metadata.journal or "unknown"
        journals[j] = journals.get(j, 0) + 1
    return dict(sorted(journals.items(), key=lambda x: x[1], reverse=True)[:10])


def map_research_density(vectors: list[PaperVector]) -> dict[str, float]:
    """Σ-13: Map research density by concept."""
    densities = {}
    total = len(vectors)
    for v in vectors:
        for c in v.concept.concepts:
            densities[c] = densities.get(c, 0) + 1
    return {c: round(n / total, 3) for c, n in densities.items()}


# =========================
# Σ-14〜Σ-19: 実験・設計系
# =========================

def score_protocol_difficulty(methods: list[str]) -> float:
    """Σ-14: Score protocol difficulty."""
    DIFFICULTY = {"scRNA-seq": 0.9, "CRISPR": 0.8, "Western blot": 0.3, "qPCR": 0.2}
    if not methods:
        return 0.5
    scores = [DIFFICULTY.get(m, 0.5) for m in methods]
    return round(sum(scores) / len(scores), 2)


def assess_reproducibility_risk(vectors: list[PaperVector]) -> dict:
    """Σ-15: Assess reproducibility risk."""
    if not vectors:
        return {"risk": 0.5, "estimated": True}

    # More methods = higher variance = higher risk
    all_methods = set()
    for v in vectors:
        all_methods.update(v.method.methods.keys())

    risk = min(1.0, len(all_methods) / 10)
    return {"risk": round(risk, 2), "method_count": len(all_methods), "estimated": True}


def enumerate_controls(experiment_type: str) -> list[str]:
    """Σ-16: Enumerate required controls."""
    CONTROLS = {
        "knockout": ["wild-type", "scramble", "heterozygous"],
        "drug": ["vehicle", "dose-response", "time-course"],
        "default": ["negative control", "positive control"],
    }
    return CONTROLS.get(experiment_type, CONTROLS["default"])


def check_sample_size(n: int, effect_size: float = 0.5) -> dict:
    """Σ-17: Check sample size adequacy."""
    # Simplified power calculation
    required = int(16 / (effect_size ** 2))
    adequate = n >= required
    return {"n": n, "required": required, "adequate": adequate, "power": min(1.0, n / required)}


def validate_stats_method(data_type: str, comparison: str) -> str:
    """Σ-18: Validate statistical method."""
    if data_type == "continuous" and comparison == "two_groups":
        return "t-test or Mann-Whitney U"
    elif data_type == "continuous" and comparison == "multiple":
        return "ANOVA with post-hoc"
    elif data_type == "categorical":
        return "Chi-square or Fisher's exact"
    return "Consult statistician"


def explain_model_reasoning(model: str, vectors: list[PaperVector]) -> str:
    """Σ-19: Explain model system reasoning."""
    count = sum(1 for v in vectors if model.lower() in str(v.metadata.species).lower())
    return f"{model}は{count}論文で使用。関連研究との整合性あり。" if count else f"{model}の使用実績なし"


# =========================
# Σ-20〜Σ-25: 論文・発表補助
# =========================

def plan_figures(vectors: list[PaperVector]) -> list[dict]:
    """Σ-20: Plan figure structure (no generation)."""
    figures = [
        {"id": 1, "type": "overview", "description": "研究全体像"},
        {"id": 2, "type": "data", "description": "主要データ"},
    ]
    if len(vectors) > 2:
        figures.append({"id": 3, "type": "comparison", "description": "比較解析"})
    return figures


def structure_graphical_abstract() -> dict:
    """Σ-21: Structure graphical abstract (no content)."""
    return {
        "sections": ["背景", "手法", "結果", "結論"],
        "layout": "horizontal_flow",
        "max_elements": 5,
    }


def check_supplement_completeness(sections: list[str]) -> list[str]:
    """Σ-22: Check supplement completeness."""
    REQUIRED = ["methods_detail", "raw_data", "statistics"]
    missing = [r for r in REQUIRED if r not in sections]
    return missing


def detect_discussion_gaps(claims: list[str], discussion: str) -> list[str]:
    """Σ-23: Detect gaps in discussion."""
    gaps = []
    for claim in claims:
        if claim.lower()[:20] not in discussion.lower():
            gaps.append(f"'{claim[:30]}...'への言及なし")
    return gaps


def flag_risky_sentences(sentences: list[str]) -> list[dict]:
    """Σ-24: Flag risky statements."""
    RISK_WORDS = ["prove", "definitive", "always", "never"]
    flagged = []
    for s in sentences:
        for w in RISK_WORDS:
            if w in s.lower():
                flagged.append({"sentence": s[:50], "risk": f"'{w}'は過度な断定"})
    return flagged


def detect_citation_bias(vectors: list[PaperVector]) -> dict:
    """Σ-25: Detect citation bias."""
    years = [v.metadata.year for v in vectors if v.metadata.year]
    if not years:
        return {"bias": "unknown"}

    avg_year = sum(years) / len(years)
    recency_bias = avg_year > 2020
    return {
        "recency_bias": recency_bias,
        "avg_year": round(avg_year, 1),
        "recommendation": "古典論文の追加を検討" if recency_bias else "バランス良好",
    }


# =========================
# Σ-26〜Σ-30: 継続・運用系
# =========================

def detect_research_drift(old_vectors: list[PaperVector], new_vectors: list[PaperVector]) -> dict:
    """Σ-26: Detect research drift over time."""
    old_concepts = set()
    new_concepts = set()

    for v in old_vectors:
        old_concepts.update(v.concept.concepts.keys())
    for v in new_vectors:
        new_concepts.update(v.concept.concepts.keys())

    added = new_concepts - old_concepts
    removed = old_concepts - new_concepts

    return {
        "drift_detected": len(added) > 0 or len(removed) > 0,
        "added_concepts": list(added),
        "removed_concepts": list(removed),
    }


def generate_periodic_review(vectors: list[PaperVector], period: str = "quarterly") -> dict:
    """Σ-27: Generate periodic review summary."""
    return {
        "period": period,
        "paper_count": len(vectors),
        "top_concepts": list(set(c for v in vectors for c in v.concept.concepts))[:5],
        "recommendation": "継続監視推奨" if len(vectors) > 5 else "データ蓄積中",
    }


def assess_field_saturation(vectors: list[PaperVector], concept: str) -> dict:
    """Σ-28: Assess field saturation."""
    relevant = [v for v in vectors for c in v.concept.concepts if concept.lower() in c.lower()]
    novelty_avg = sum(v.temporal.novelty for v in relevant) / max(len(relevant), 1)

    saturation = 1 - novelty_avg
    return {
        "concept": concept,
        "saturation": round(saturation, 2),
        "interpretation": "飽和状態" if saturation > 0.7 else "成長余地あり",
    }


def detect_new_concepts(old_vectors: list[PaperVector], new_vectors: list[PaperVector]) -> list[str]:
    """Σ-29: Detect newly emerging concepts."""
    old_concepts = set(c for v in old_vectors for c in v.concept.concepts)
    new_concepts = set(c for v in new_vectors for c in v.concept.concepts)
    return list(new_concepts - old_concepts)


def sync_research_log(vectors: list[PaperVector]) -> dict:
    """Σ-30: Sync research log status."""
    return {
        "total": len(vectors),
        "with_year": sum(1 for v in vectors if v.metadata.year),
        "with_concepts": sum(1 for v in vectors if v.concept.concepts),
        "sync_status": "complete",
    }
