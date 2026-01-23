"""Golden Path Test for Reporting (PR-3)."""
import pytest
from jarvis_core.report.generator import ReportGenerator, generate_report_with_evidence
from jarvis_core.renderers.report_renderer import render_claimset_report, render_comparison_report

@pytest.fixture
def sample_data():
    query = "What are the effects of AI on research productivity?"
    claims = [
        {
            "claim_id": "claim_001",
            "claim_text": "AI significantly increases data analysis speed.",
            "claim_type": "Fact",
            "type": "fact", # For renderer
            "text": "AI significantly increases data analysis speed."
        },
        {
            "claim_id": "claim_002",
            "claim_text": "AI might lead to automated hypothesis generation.",
            "claim_type": "Interpretation",
            "type": "interpretation",
            "text": "AI might lead to automated hypothesis generation."
        }
    ]
    evidence_list = [
        {
            "evidence_id": "ev_001",
            "claim_id": "claim_001",
            "paper_id": "paper_A",
            "evidence_strength": "High",
            "quote_span": "Study A shows 50% increase in speed.",
            "quote": "Study A shows 50% increase in speed.",
            "locator": "Page 5"
        }
    ]
    papers = [
        {
            "paper_id": "paper_A",
            "title": "AI in Science",
            "authors": ["Alice", "Bob"],
            "year": 2023
        }
    ]
    return query, claims, evidence_list, papers

def test_report_generator(sample_data):
    query, claims, evidence_list, papers = sample_data
    generator = ReportGenerator()
    report = generator.generate_full_report(query, claims, evidence_list, papers)
    
    assert "# Research Report" in report
    assert "claim_001" in report or "ev_001"[:8] in report
    assert "AI significantly increases data analysis speed." in report
    assert "paper_A" in report
    assert "Support Rate: 50.0%" in report

def test_generate_report_with_evidence_convenience(sample_data):
    query, claims, evidence_list, papers = sample_data
    report = generate_report_with_evidence(query, claims, evidence_list, papers)
    assert "JARVIS Research OS (Phase 2)" in report

def test_report_renderer_claimset(sample_data):
    query, claims, evidence_list, papers = sample_data
    # Convert evidence list to dict for renderer
    evidence_dict = {ev["evidence_id"]: ev for ev in evidence_list}
    
    report = render_claimset_report(query, claims, evidence_dict)
    
    assert "# Research Summary" in report
    assert "Executive Summary" in report
    assert "Key Findings" in report
    assert "Facts:** 1" in report
    assert "Interpretations:** 1" in report

def test_report_renderer_comparison():
    query = "Comparison of Large Language Models"
    papers = [
        {"paper_id": "p1", "title": "Model A Paper"},
        {"paper_id": "p2", "title": "Model B Paper"}
    ]
    matrix = {
        "p1": {"Accuracy": "85%", "Latency": "100ms"},
        "p2": {"Accuracy": "90%", "Latency": "150ms"}
    }
    
    report = render_comparison_report(query, papers, matrix)
    
    assert "# Paper Comparison" in report
    assert "| Paper | Accuracy | Latency |" in report
    assert "| Model A Paper | 85% | 100ms |" in report
    assert "| Model B Paper | 90% | 150ms |" in report
