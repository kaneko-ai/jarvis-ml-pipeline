"""Feature Extraction Stage (Domain-Specific).

Extracts domain-specific features (Rubrics) from papers.
For Immuno-Oncology: model_tier, evidence_type, causal_strength, etc.

Output: features.jsonl (one per paper)
"""
from typing import Any, Dict, List
import uuid
from jarvis_core.pipelines.stage_registry import register_stage
from jarvis_core.task import TaskContext, Artifacts


def extract_immuno_onco_features(paper: Dict) -> Dict[str, Any]:
    """Extract immuno-oncology rubric features from paper metadata.
    
    In production, this would use LLM or ML classifier.
    For Phase 2 bootstrap, we use heuristics based on keywords.
    """
    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()
    text = title + " " + abstract
    
    # Heuristic classification (to be replaced with LLM)
    features = {
        "paper_id": paper.get("paper_id"),
        "model_tier": "unknown",
        "evidence_type": "unknown",
        "causal_strength": "association",  # default conservative
        "reproducibility": "single",
        "tme_relevance": "none"
    }
    
    # Model tier detection
    if "randomized" in text or "rct" in text or "phase iii" in text:
        features["model_tier"] = "rct"
    elif "clinical trial" in text or "phase ii" in text or "phase i" in text:
        features["model_tier"] = "clinical_trial"
    elif "patient" in text or "cohort" in text:
        features["model_tier"] = "patient"
    elif "mouse" in text or "mice" in text or "murine" in text:
        features["model_tier"] = "mouse"
    elif "organoid" in text:
        features["model_tier"] = "organoid"
    elif "cell line" in text or "in vitro" in text:
        features["model_tier"] = "cell_line"
    
    # Evidence type
    if "survival" in text or "response rate" in text:
        features["evidence_type"] = "clinical"
    elif "imaging" in text or "ihc" in text or "immunohistochemistry" in text:
        features["evidence_type"] = "imaging"
    elif "functional" in text or "cytotoxicity" in text or "killing" in text:
        features["evidence_type"] = "functional"
    elif "rna-seq" in text or "sequencing" in text:
        features["evidence_type"] = "seq_data"
    elif "flow cytometry" in text or "facs" in text:
        features["evidence_type"] = "flow_cyto"
    
    # Causal strength
    if "knockout" in text or "crispr" in text or "inhibitor" in text or "blockade" in text:
        if "mechanism" in text:
            features["causal_strength"] = "causal"
        else:
            features["causal_strength"] = "intervention"
    
    # Reproducibility
    if "multicenter" in text or "validation cohort" in text or "independent" in text:
        features["reproducibility"] = "multi_cohort"
    elif "replicate" in text or "repeated" in text:
        features["reproducibility"] = "replicated"
    
    # TME relevance
    if "tumor microenvironment" in text or "tme" in text:
        if "interaction" in text or "crosstalk" in text:
            features["tme_relevance"] = "high"
        else:
            features["tme_relevance"] = "limited"
    
    return features


@register_stage("extraction.rubric_features")
def extract_features(context: TaskContext, artifacts: Artifacts) -> Dict[str, Any]:
    """Extract rubric-based features from papers."""
    
    papers = artifacts.get("papers", [])
    features_list = []
    
    for paper in papers:
        features = extract_immuno_onco_features(paper)
        features_list.append(features)
    
    # Store in artifacts
    artifacts["features"] = features_list
    
    # Provenance
    context.provenance.add("features.jsonl", "extraction.rubric_features")
    
    return {
        "count": len(features_list),
        "rubric": "immuno_onco_v1"
    }
