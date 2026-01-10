"""Tests for style.checklists module."""

from jarvis_core.style.checklists import (
    CHECKLISTS,
    run_checklists,
    _dose_dependent_consistent,
)


class TestDoseDependentConsistent:
    def test_no_dose_dependent_text(self):
        result = _dose_dependent_consistent({"text": "Normal content"})
        assert result is True

    def test_consistent_dose_dependent(self):
        result = _dose_dependent_consistent({"text": "濃度依存的効果を観察した"})
        assert result is True

    def test_inconsistent_dose_dependent(self):
        result = _dose_dependent_consistent({"text": "濃度依存性の効果があった"})
        assert result is False


class TestChecklists:
    def test_checklists_defined(self):
        assert len(CHECKLISTS) >= 5
        assert all("id" in item for item in CHECKLISTS)
        assert all("description" in item for item in CHECKLISTS)
        assert all("check" in item for item in CHECKLISTS)


class TestRunChecklists:
    def test_all_pass(self):
        qa_result = {
            "counts": {
                "term_variant": 0,
                "abbrev_missing": 0,
                "missing_reference": 0,
            },
            "conclusion_sentences": 5,
            "normalized_text": {},
        }
        
        results = run_checklists(qa_result)
        
        assert len(results) == len(CHECKLISTS)
        assert all(r["passed"] for r in results)

    def test_term_variant_fail(self):
        qa_result = {
            "counts": {"term_variant": 3},
            "conclusion_sentences": 5,
        }
        
        results = run_checklists(qa_result)
        
        no_term_result = next(r for r in results if r["id"] == "no_term_variants")
        assert no_term_result["passed"] is False

    def test_conclusion_minimum_fail(self):
        qa_result = {
            "counts": {},
            "conclusion_sentences": 1,
        }
        
        results = run_checklists(qa_result)
        
        conclusion_result = next(r for r in results if r["id"] == "conclusion_minimum")
        assert conclusion_result["passed"] is False

    def test_result_structure(self):
        results = run_checklists({})
        
        for result in results:
            assert "id" in result
            assert "description" in result
            assert "passed" in result
