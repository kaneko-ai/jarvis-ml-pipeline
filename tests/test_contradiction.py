"""Tests for truth.contradiction module."""

from unittest.mock import MagicMock

from jarvis_core.truth.contradiction import (
    ContradictionResult,
    find_shared_concepts,
    check_antonym_pattern,
    detect_contradictions,
    summarize_contradictions,
)


class TestContradictionResult:
    def test_to_dict(self):
        result = ContradictionResult(
            fact1="Drug A increases tumor growth",
            fact2="Drug A decreases tumor growth",
            contradiction_type="antonym_pattern: increase vs decrease",
            confidence=0.5,
            shared_concept="tumor",
        )
        d = result.to_dict()
        assert d["fact1"] == "Drug A increases tumor growth"
        assert d["contradiction_type"] == "antonym_pattern: increase vs decrease"
        assert d["confidence"] == 0.5


class TestFindSharedConcepts:
    def test_shared_concepts_found(self):
        text1 = "The treatment increases tumor growth significantly"
        text2 = "The drug decreases tumor size effectively"

        shared = find_shared_concepts(text1, text2)
        assert "tumor" in shared

    def test_no_shared_concepts(self):
        text1 = "Apples are healthy"
        text2 = "Cars need gasoline"

        shared = find_shared_concepts(text1, text2)
        assert len(shared) == 0

    def test_stopwords_filtered(self):
        text1 = "The drug is effective"
        text2 = "The treatment is working"

        shared = find_shared_concepts(text1, text2)
        assert "the" not in shared
        assert "is" not in shared


class TestCheckAntonymPattern:
    def test_increase_decrease_pattern(self):
        has_antonym, pattern = check_antonym_pattern(
            "Drug increases activity", "Drug decreases activity"
        )
        assert has_antonym is True
        assert "increase" in pattern and "decrease" in pattern

    def test_activate_inhibit_pattern(self):
        has_antonym, pattern = check_antonym_pattern(
            "Compound activates the pathway", "Compound inhibits the pathway"
        )
        assert has_antonym is True

    def test_no_antonym_pattern(self):
        has_antonym, pattern = check_antonym_pattern(
            "Drug affects the cell", "Drug modifies the cell"
        )
        assert has_antonym is False
        assert pattern == ""


class TestDetectContradictions:
    def test_detect_with_antonym(self):
        fact1 = MagicMock()
        fact1.statement = "Treatment A increases tumor growth"

        fact2 = MagicMock()
        fact2.statement = "Treatment A decreases tumor growth"

        contradictions = detect_contradictions([fact1, fact2])

        assert len(contradictions) == 1
        assert "increase" in contradictions[0].contradiction_type

    def test_no_contradiction(self):
        fact1 = MagicMock()
        fact1.statement = "Drug A targets cancer cells"

        fact2 = MagicMock()
        fact2.statement = "Drug B affects immune response"

        contradictions = detect_contradictions([fact1, fact2])
        assert len(contradictions) == 0

    def test_single_fact_returns_empty(self):
        fact = MagicMock()
        fact.statement = "Some statement"

        contradictions = detect_contradictions([fact])
        assert contradictions == []

    def test_empty_facts_returns_empty(self):
        contradictions = detect_contradictions([])
        assert contradictions == []


class TestSummarizeContradictions:
    def test_summarize_with_results(self):
        results = [
            ContradictionResult(
                fact1="A increases X",
                fact2="A decreases X",
                contradiction_type="antonym",
                confidence=0.5,
                shared_concept="X",
            )
        ]
        summary = summarize_contradictions(results)

        assert "潜在的な矛盾" in summary
        assert "検出数: 1" in summary
        assert "X" in summary

    def test_summarize_empty_results(self):
        summary = summarize_contradictions([])
        assert "検出されませんでした" in summary