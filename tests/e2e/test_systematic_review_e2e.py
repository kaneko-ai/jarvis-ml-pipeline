from __future__ import annotations

import json

import pytest

from jarvis_core.advanced.features import SystematicReviewAgent
from jarvis_core.bundle.assembler import BundleAssembler
from jarvis_core.evidence.ensemble import grade_evidence
from jarvis_core.experimental.prisma.generator import PRISMAData, generate_prisma_flow


@pytest.mark.e2e
def test_systematic_review_e2e(tmp_path):
    query = "Does treatment X improve outcomes?"

    # 1. Query input
    context = {
        "run_id": "e2e-001",
        "goal": query,
        "query": query,
        "pipeline": "systematic_review",
        "timestamp": "2025-01-01T00:00:00Z",
        "model": "test",
    }

    # 2. Mock paper search
    papers = [
        {"paper_id": "p1", "title": "Study A", "abstract": "We ran an RCT."},
        {"paper_id": "p2", "title": "Study B", "abstract": "Observational study."},
    ]

    # 3. Evidence grading
    grades = [
        grade_evidence(title=paper["title"], abstract=paper["abstract"], use_llm=False)
        for paper in papers
    ]

    # 4. PRISMA flow generation
    review = SystematicReviewAgent()
    for paper in papers:
        review.add_paper(paper["paper_id"], paper, stage="identification")
        review.advance_stage(paper["paper_id"])
    prisma_counts = review.get_prisma_flow()

    prisma_data = PRISMAData(
        identification_database=prisma_counts.get("identification", 0),
        identification_other=0,
        duplicates_removed=0,
        records_screened=prisma_counts.get("screening", 0),
        records_excluded_screening=0,
        full_text_assessed=0,
        full_text_excluded=0,
        studies_included=prisma_counts.get("included", 0),
    )
    prisma_mermaid = generate_prisma_flow(prisma_data, format="mermaid")

    # 5. Final report output
    report = "\n".join(
        [
            "# Systematic Review",
            f"Query: {query}",
            "",
            "## Evidence",
            json.dumps([grade.level.value for grade in grades]),
            "",
            "## PRISMA",
            prisma_mermaid,
        ]
    )

    artifacts = {
        "papers": papers,
        "claims": [{"claim_text": "Evidence graded", "evidence_ids": ["p1", "p2"]}],
        "evidence": [
            {"paper_id": paper["paper_id"], "grade": grade.level.value}
            for paper, grade in zip(papers, grades)
        ],
        "scores": {"quality": 0.9},
        "warnings": [],
        "answer": report,
        "citations": [],
    }

    assembler = BundleAssembler(tmp_path)
    generated = assembler.build(context, artifacts)

    assert set(assembler.REQUIRED_ARTIFACTS).issubset(set(generated))
    for required in assembler.REQUIRED_ARTIFACTS:
        assert (tmp_path / required).exists()