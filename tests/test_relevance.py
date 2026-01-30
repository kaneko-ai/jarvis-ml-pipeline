"""Tests for truth.relevance module."""

from jarvis_core.truth.relevance import (
    bm25_score,
    jaccard_similarity,
    score_relevance,
    filter_by_relevance,
)


class TestBm25Score:
    def test_matching_terms(self):
        score = bm25_score("machine learning", "machine learning algorithms")
        assert score > 0

    def test_no_matching_terms(self):
        score = bm25_score("apple banana", "car house tree")
        assert score == 0.0

    def test_empty_document(self):
        score = bm25_score("query", "")
        assert score == 0.0

    def test_multiple_occurrences(self):
        score1 = bm25_score("cancer", "cancer treatment")
        score2 = bm25_score("cancer", "cancer cancer therapy")

        # More occurrences should generally give higher score
        assert score2 >= score1


class TestJaccardSimilarity:
    def test_identical_texts(self):
        sim = jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_no_overlap(self):
        sim = jaccard_similarity("apple banana", "car house")
        assert sim == 0.0

    def test_partial_overlap(self):
        sim = jaccard_similarity("cat dog bird", "cat fish dog")
        assert 0 < sim < 1

    def test_empty_text(self):
        sim = jaccard_similarity("", "some text")
        assert sim == 0.0


class TestScoreRelevance:
    def test_relevant_text(self):
        result = score_relevance(
            "cancer treatment efficacy", "Study on cancer treatment and its efficacy in patients"
        )
        assert result["score"] > 0
        assert result["method"] == "bm25+jaccard"
        assert "bm25" in result
        assert "jaccard" in result

    def test_irrelevant_text(self):
        result = score_relevance(
            "quantum computing algorithms", "Recipe for chocolate cake with vanilla frosting"
        )
        assert result["score"] < 0.3
        assert result["threshold_met"] is False

    def test_empty_query(self):
        result = score_relevance("", "Some evidence text")
        assert result["score"] == 0.0
        assert result["method"] == "none"

    def test_empty_evidence(self):
        result = score_relevance("Some query", "")
        assert result["score"] == 0.0


class TestFilterByRelevance:
    def test_filter_relevant_evidences(self):
        evidences = [
            ("e1", "cancer treatment therapy"),
            ("e2", "cooking recipes for dinner"),
            ("e3", "cancer research breakthrough"),
        ]

        results = filter_by_relevance("cancer treatment", evidences, min_score=0.2)

        # Should include cancer-related evidences
        result_ids = [r[0] for r in results]
        assert "e1" in result_ids
        assert "e3" in result_ids

    def test_filter_empty_evidences(self):
        results = filter_by_relevance("query", [], min_score=0.3)
        assert results == []

    def test_results_sorted_by_score(self):
        evidences = [
            ("e1", "partial match"),
            ("e2", "exact query match query"),
            ("e3", "query query query"),
        ]

        results = filter_by_relevance("query", evidences, min_score=0.0)

        if len(results) > 1:
            # Should be sorted descending
            scores = [r[1] for r in results]
            assert scores == sorted(scores, reverse=True)
