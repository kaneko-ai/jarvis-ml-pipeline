from __future__ import annotations

from jarvis_core.stages.extract_features import extract_features, extract_immuno_onco_features


def test_extract_immuno_onco_features_rct_and_clinical_and_causal() -> None:
    features = extract_immuno_onco_features(
        {
            "paper_id": "p1",
            "title": "Randomized phase III trial with survival benefit",
            "abstract": "CRISPR mechanism and tumor microenvironment interaction multicenter",
        }
    )

    assert features["paper_id"] == "p1"
    assert features["model_tier"] == "rct"
    assert features["evidence_type"] == "clinical"
    assert features["causal_strength"] == "causal"
    assert features["reproducibility"] == "multi_cohort"
    assert features["tme_relevance"] == "high"


def test_extract_immuno_onco_features_other_paths() -> None:
    mouse = extract_immuno_onco_features(
        {
            "paper_id": "p2",
            "title": "Mouse model study",
            "abstract": "flow cytometry replicate",
        }
    )
    assert mouse["model_tier"] == "mouse"
    assert mouse["evidence_type"] == "flow_cyto"
    assert mouse["reproducibility"] == "replicated"

    organoid = extract_immuno_onco_features(
        {
            "paper_id": "p3",
            "title": "Organoid and in vitro",
            "abstract": "RNA-seq analysis",
        }
    )
    # organoid branch comes before cell line
    assert organoid["model_tier"] == "organoid"
    assert organoid["evidence_type"] == "seq_data"


def test_extract_features_wrapped_entrypoint() -> None:
    papers = [
        {"paper_id": "p1", "title": "clinical trial", "abstract": "response rate"},
        {"paper_id": "p2", "title": "patient cohort", "abstract": "imaging"},
    ]

    result = extract_features.__wrapped__(papers)
    assert result["count"] == 2
    assert result["rubric"] == "immuno_onco_v1"
    assert result["stage"] == "extraction.rubric_features"
    assert len(result["features"]) == 2


def test_extract_features_wrapped_accepts_kwargs() -> None:
    result = extract_features.__wrapped__(
        [{"paper_id": "p3", "title": "mouse", "abstract": "functional"}],
        custom="x",
    )
    assert result["count"] == 1
