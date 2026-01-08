"""Example: Generate Report with Evidence IDs.

Demonstrates how to use the Phase 2 Report Generator
to create  reports with automatic evidence annotations.
"""
from jarvis_core.report.generator import generate_report_with_evidence


# Sample data (would come from actual pipeline execution)
SAMPLE_QUERY = "CD73 immunotherapy for solid tumors"

SAMPLE_CLAIMS = [
    {
        "claim_id": "claim_001",
        "claim_text": "CD73 is highly expressed in the tumor microenvironment",
        "claim_type": "Mechanism",
        "confidence_self": 0.9
    },
    {
        "claim_id": "claim_002",
        "claim_text": "CD73 inhibition enhances anti-tumor T cell responses",
        "claim_type": "Mechanism",
        "confidence_self": 0.85
    },
    {
        "claim_id": "claim_003",
        "claim_text": "Combination of CD73 inhibitors with PD-1 blockade showed clinical benefit",
        "claim_type": "Efficacy",
        "confidence_self": 0.8
    },
    {
        "claim_id": "claim_004",
        "claim_text": "CD73 expression correlates with poor prognosis in multiple cancer types",
        "claim_type": "Biomarker",
        "confidence_self": 0.75
    },
]

SAMPLE_EVIDENCE = [
    {
        "evidence_id": "ev_a1b2c3d4",
        "claim_id": "claim_001",
        "paper_id": "PMID:36991446",
        "evidence_strength": "Strong",
        "quote_span": "CD73 is expressed on various cell types including tumor cells, regulatory T cells, and myeloid-derived suppressor cells."
    },
    {
        "evidence_id": "ev_e5f6g7h8",
        "claim_id": "claim_001",
        "paper_id": "PMID:36451063",
        "evidence_strength": "Medium",
        "quote_span": "High CD73 expression in the TME contributes to immune evasion."
    },
    {
        "evidence_id": "ev_i9j0k1l2",
        "claim_id": "claim_002",
        "paper_id": "PMID:35982657",
        "evidence_strength": "Strong",
        "quote_span": "CD73 blockade restored T cell effector functions and enhanced anti-tumor responses in preclinical models."
    },
    {
        "evidence_id": "ev_m3n4o5p6",
        "claim_id": "claim_003",
        "paper_id": "PMID:35982657",
        "evidence_strength": "Medium",
        "quote_span": "Phase I/II trial showed objective responses in 30% of patients when oleclumab was combined with durvalumab."
    },
    {
        "evidence_id": "ev_q7r8s9t0",
        "claim_id": "claim_004",
        "paper_id": "PM ID:35546572",
        "evidence_strength": "Medium",
        "quote_span": "CD73 expression was significantly associated with reduced overall survival (HR=1.45, p=0.02)."
    },
]

SAMPLE_PAPERS = [
    {
        "paper_id": "PMID:36991446",
        "title": "CD73 in tumor immunology and immunotherapy",
        "authors": ["Zhang Y", "Wang X"],
        "year": 2023
    },
    {
        "paper_id": "PMID:36451063",
        "title": "Adenosine pathway in cancer immunity",
        "authors": ["Chen L", "Huang M"],
        "year": 2022
    },
    {
        "paper_id": "PMID:35982657",
        "title": "CD73 inhibition for solid tumors",
        "authors": ["Park J", "Kim S"],
        "year": 2022
    },
    {
        "paper_id": "PMID:35546572",
        "title": "T cell exhaustion and adenosine signaling",
        "authors": ["Liu W", "Zhang H"],
        "year": 2022
    },
]


def main():
    """Generate and display sample report."""
    print("Generating Phase 2 Report with Evidence IDs...\n")

    report = generate_report_with_evidence(
        query=SAMPLE_QUERY,
        claims=SAMPLE_CLAIMS,
        evidence=SAMPLE_EVIDENCE,
        papers=SAMPLE_PAPERS
    )

    print(report)

    # Save to file
    output_file = "sample_report_phase2.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Report saved to: {output_file}")


if __name__ == "__main__":
    main()
