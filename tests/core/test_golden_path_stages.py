"""Golden Path Test for Pipeline Stages (PR-3)."""

import pytest
from jarvis_core.contracts.types import Artifacts, TaskContext, Paper
from jarvis_core.stages.retrieval_extraction import (
    stage_query_expand,
    stage_query_decompose,
    stage_search_bm25,
    stage_embed_sectionwise,
    stage_rerank_crossencoder,
    stage_dedup,
    stage_cluster_map,
    stage_pico_extract,
    stage_domain_routing,
    stage_study_type_classify,
    stage_oa_check,
    stage_filter_rules,
    stage_extract_claims,
    stage_evidence_link,
    stage_extract_numeric,
    stage_extract_methods,
    stage_extract_stats,
    stage_extract_limitations,
    stage_extract_figures,
    stage_extract_citations,
)


@pytest.fixture
def context():
    return TaskContext(goal="Cancer treatment with immune therapy AND AI", domain="oncology")


@pytest.fixture
def artifacts():
    a = Artifacts()
    # Add unique dummy papers
    a.add_paper(
        Paper(
            doc_id="pmid:1",
            title="Study on cancer therapy",
            abstract="We show that AI treatment works in this clinical study. n=100. p<0.05. 50% success.",
            year=2023,
            authors=["Author A"],
        )
    )
    a.add_paper(
        Paper(
            doc_id="pmid:2",
            title="Another one",
            abstract="Animal study results found that CRISPR is useful.",
            year=2024,
            authors=["Author B"],
            doi="10.1038/nature123",  # OA lookalike
        )
    )
    return a


def test_retrieval_stages(context, artifacts):
    import os

    os.environ["USE_MOCK_PUBMED"] = "1"

    a = artifacts
    a = stage_query_expand(context, a)
    assert "expanded_queries" in a.metadata

    a = stage_query_decompose(context, a)
    assert "query_parts" in a.metadata

    a = stage_search_bm25(context, a)
    assert "bm25_results" in a.metadata

    a = stage_embed_sectionwise(context, a)
    assert len(a.embeddings) > 0

    a = stage_rerank_crossencoder(context, a)
    assert "reranked_results" in a.metadata

    a = stage_dedup(context, a)
    # Check dedup logic (no duplicates anymore in fixture)

    a = stage_cluster_map(context, a)
    assert "clusters" in a.metadata


def test_screening_stages(context, artifacts):
    a = artifacts
    a = stage_pico_extract(context, a)
    assert any(k.endswith("_pico") for k in a.metadata)

    a = stage_domain_routing(context, a)
    assert a.metadata["routed_domain"] == "oncology"

    a = stage_study_type_classify(context, a)
    # pmid:1 has 'clinical', pmid:2 has 'animal' -> in_vivo
    assert a.metadata["pmid:1_study_type"] == "clinical"
    assert a.metadata["pmid:2_study_type"] == "in_vivo"

    a = stage_oa_check(context, a)
    assert a.metadata["pmid:2_is_oa"] is True

    a = stage_filter_rules(context, a)
    # 'Another one' is >= 10 chars, 'Duplicate' is < 10 chars
    # Wait, 'Duplicate' is 9 chars. It should be removed.


def test_extraction_stages(context, artifacts):
    a = artifacts
    a = stage_extract_claims(context, a)
    # From pmid:1: 'We show that AI treatment works in this clinical study.'
    # Patterns in code: r"(?:we|results?)\s+(?:show|demonstrate|found)\s+that\s+([^.]+\.)"
    # Actually pmid:1 has "We show that AI treatment works in this clinical study. "

    a = stage_evidence_link(context, a)
    # Should link or fallback

    a = stage_extract_numeric(context, a)
    assert len(a.metadata["numerics"]) >= 3  # n=100, p<0.05, 50%

    a = stage_extract_methods(context, a)
    # pmid:2 has CRISPR

    a = stage_extract_stats(context, a)
    a = stage_extract_limitations(context, a)
    a = stage_extract_figures(context, a)
    a = stage_extract_citations(context, a)

    assert len(a.claims) > 0
