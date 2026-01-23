"""Golden Path Test for Advanced Modules (PR-3)."""
import pytest
from jarvis_core.feasibility import score_feasibility
from jarvis_core.reporting.rank_explain import (
    calculate_average_subscores,
    explain_ranking,
    format_subscores_markdown,
    validate_subscores
)
from jarvis_core.runtime.failure_signal import FailureSignal, FailureCode, FailureStage, extract_failure_signals

def test_feasibility_scoring():
    class MockVector:
        def __init__(self, concepts, methods):
            self.concept = type('obj', (), {'concepts': concepts})
            self.method = type('obj', (), {'methods': methods})
            
    vectors = [
        MockVector(["Cancer", "Genetics"], ["CRISPR", "Sequencing"]),
        MockVector(["Genetics"], ["PCR"])
    ]
    
    # Test valid hypothesis
    res = score_feasibility("Cancer genetics using CRISPR", vectors)
    assert res["overall"] > 0
    assert res["related_papers"] == 2
    assert "難度" in res["reason"] or "先行研究" in res["reason"] or "高コスト" in res["reason"]
    
    # Test empty hypothesis
    res_empty = score_feasibility("", vectors)
    assert res_empty["overall"] == 0.5
    assert res_empty["reason"] == "仮説が不明"

def test_ranking_explanation():
    papers = [
        {"paper_id": "p1", "subscores": {"novelty": 0.8, "reproducibility": 0.4}},
        {"paper_id": "p2", "subscores": {"novelty": 0.4, "reproducibility": 0.8}}
    ]
    
    averages = calculate_average_subscores(papers)
    assert averages["novelty"] == pytest.approx(0.6)
    assert averages["reproducibility"] == pytest.approx(0.6)
    
    exp = explain_ranking(papers[0], averages)
    assert "novelty" in exp["strengths"]
    assert "reproducibility" in exp["weaknesses"]
    assert "主な強み" in exp["explanation"]

def test_subscore_validation():
    valid_paper = {"paper_id": "v", "subscores": {"novelty": 0.5}}
    invalid_paper = {"paper_id": "i", "subscores": {"novelty": 1.5}} # Out of range
    
    assert len(validate_subscores(valid_paper)) == 0
    assert len(validate_subscores(invalid_paper)) > 0
    assert len(validate_subscores({})) > 0

def test_failure_signal():
    # Test from exception
    sig = FailureSignal.from_exception(TimeoutError("Too slow"), stage=FailureStage.FETCH)
    assert sig.code == FailureCode.TIMEOUT
    assert sig.stage == FailureStage.FETCH
    
    # Test from result error
    sig2 = FailureSignal.from_result_error("ExtractError", "Failed to parse", stage="extract")
    assert sig2.code == FailureCode.EXTRACT_PDF_FAILED
    assert sig2.stage == FailureStage.EXTRACT
    
    # Test extraction
    class MockResult:
        def __init__(self, error=None, value=None):
            self.error = error
            self.value = value
            
    class MockValue:
        def __init__(self, gate_results):
            self.gate_results = gate_results
            
    res = MockResult(value=MockValue({"citation": False}))
    signals = extract_failure_signals(res)
    assert len(signals) == 1
    assert signals[0].code == FailureCode.CITATION_GATE_FAILED
