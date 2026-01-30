"""Tests for AI features module."""

from jarvis_core.ai.features import (
    AutoTagger,
    CitationGenerator,
    KeywordExtractor,
    PaperQA,
    PaperTranslator,
    SentimentAnalyzer,
    SimilarityCalculator,
    get_auto_tagger,
    get_citation_generator,
    get_keyword_extractor,
    get_sentiment_analyzer,
)
import pytest


class TestAutoTagger:
    """Test auto-tagging functionality."""

    def test_get_tags_ai(self):
        """Test AI tag detection."""
        tagger = AutoTagger()
        text = "Deep learning for medical image analysis"
        tags = tagger.get_tags(text)
        assert "AI" in tags

    def test_get_tags_clinical(self):
        """Test clinical tag detection."""
        tagger = AutoTagger()
        text = "Clinical trial results for patient treatment"
        tags = tagger.get_tags(text)
        assert "Clinical" in tags

    def test_get_tags_covid(self):
        """Test COVID-19 tag detection."""
        tagger = AutoTagger()
        text = "COVID-19 vaccine development"
        tags = tagger.get_tags(text)
        assert "COVID-19" in tags

    def test_get_tags_default(self):
        """Test default tag for unrecognized text."""
        tagger = AutoTagger()
        text = "Random unrelated content"
        tags = tagger.get_tags(text)
        assert "General" in tags

    def test_tag_paper(self):
        """Test tagging a paper."""
        tagger = AutoTagger()
        paper = {"title": "Machine learning in oncology", "abstract": "Cancer treatment"}
        result = tagger.tag_paper(paper)
        assert "tags" in result
        assert "AI" in result["tags"]
        assert "Cancer" in result["tags"]


class TestKeywordExtractor:
    """Test keyword extraction."""

    def test_extract_keywords(self):
        """Test basic keyword extraction."""
        extractor = KeywordExtractor()
        text = "Machine learning machine learning deep learning neural network"
        keywords = extractor.extract(text, 3)
        assert len(keywords) > 0
        # Check that expected keywords are in the results (order may vary)
        keyword_names = [k[0] for k in keywords]
        assert "machine" in keyword_names or "learning" in keyword_names

    def test_extract_filters_stopwords(self):
        """Test stopword filtering."""
        extractor = KeywordExtractor()
        text = "The study uses methods for analysis"
        keywords = [k for k, _ in extractor.extract(text, 10)]
        assert "the" not in keywords
        assert "study" not in keywords  # Common research word

    def test_extract_phrases(self):
        """Test phrase extraction."""
        extractor = KeywordExtractor()
        text = "deep learning deep learning neural networks"
        phrases = extractor.extract_phrases(text, 2)
        assert len(phrases) > 0


class TestSentimentAnalyzer:
    """Test sentiment analysis."""

    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        analyzer = SentimentAnalyzer()
        text = "This significant study shows promising and effective results"
        result = analyzer.analyze(text)
        assert result["sentiment"] in ["Positive", "Mixed"]
        assert result["positive_indicators"] > 0

    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        analyzer = SentimentAnalyzer()
        text = "The results were limited and problematic with poor outcomes"
        result = analyzer.analyze(text)
        assert result["sentiment"] in ["Negative", "Mixed"]
        assert result["negative_indicators"] > 0

    def test_neutral_sentiment(self):
        """Test neutral sentiment."""
        analyzer = SentimentAnalyzer()
        text = "The experiment was conducted last Tuesday"
        result = analyzer.analyze(text)
        assert result["sentiment"] == "Neutral"


class TestCitationGenerator:
    """Test citation generation."""

    def test_apa_format(self):
        """Test APA citation format."""
        generator = CitationGenerator()
        paper = {
            "title": "Test Paper",
            "authors": "Smith J, Johnson A",
            "year": 2024,
            "journal": "Nature",
        }
        citation = generator.generate(paper, "apa")
        assert "Smith J, Johnson A" in citation
        assert "2024" in citation
        assert "Nature" in citation

    def test_bibtex_format(self):
        """Test BibTeX format."""
        generator = CitationGenerator()
        paper = {
            "title": "Test Paper",
            "authors": "Smith J",
            "year": 2024,
            "journal": "Science",
            "pmid": "12345",
        }
        citation = generator.generate(paper, "bibtex")
        assert "@article{" in citation
        assert "title={Test Paper}" in citation

    def test_generate_all(self):
        """Test generating all formats."""
        generator = CitationGenerator()
        paper = {"title": "Test", "authors": "A B", "year": 2024, "journal": "J"}
        all_citations = generator.generate_all(paper)
        assert "apa" in all_citations
        assert "mla" in all_citations
        assert "bibtex" in all_citations
        assert "chicago" in all_citations


class TestPaperTranslator:
    """Test paper translation."""

    def test_translate_keywords(self):
        """Test keyword translation."""
        translator = PaperTranslator()
        translations = translator.translate_keywords("cancer treatment", "ja")
        assert "cancer" in translations
        assert "treatment" in translations

    def test_add_translations(self):
        """Test adding translations to text."""
        translator = PaperTranslator()
        result = translator.add_translations("Cancer treatment study")
        assert "がん" in result or "治療" in result


class TestSimilarityCalculator:
    """Test similarity calculation."""

    def test_jaccard_similarity_same(self):
        """Test similarity of identical texts."""
        calc = SimilarityCalculator()
        score = calc.jaccard_similarity("hello world test", "hello world test")
        assert score == 1.0

    def test_jaccard_similarity_different(self):
        """Test similarity of different texts."""
        calc = SimilarityCalculator()
        score = calc.jaccard_similarity("machine learning", "quantum physics")
        assert score < 0.5

    def test_compare_papers(self):
        """Test paper comparison."""
        calc = SimilarityCalculator()
        paper1 = {"title": "Machine learning in medicine", "abstract": "AI healthcare"}
        paper2 = {"title": "Deep learning for diagnosis", "abstract": "ML medicine"}
        result = calc.compare_papers(paper1, paper2)
        assert "similarity_score" in result
        assert "similarity_level" in result


class TestPaperQA:
    """Test paper Q&A."""

    def test_answer_author_question(self):
        """Test answering author question."""
        qa = PaperQA()
        qa.set_context(
            {"title": "Test", "authors": "Smith J", "abstract": "", "journal": "", "year": ""}
        )
        answer = qa.answer("Who wrote this paper?")
        assert "Smith J" in answer

    def test_answer_year_question(self):
        """Test answering year question."""
        qa = PaperQA()
        qa.set_context(
            {"title": "Test", "authors": "", "abstract": "", "journal": "", "year": 2024}
        )
        answer = qa.answer("When was this published?")
        assert "2024" in answer


class TestFactoryFunctions:
    """Test factory functions."""

    def test_get_auto_tagger(self):
        assert isinstance(get_auto_tagger(), AutoTagger)

    def test_get_keyword_extractor(self):
        assert isinstance(get_keyword_extractor(), KeywordExtractor)

    def test_get_citation_generator(self):
        assert isinstance(get_citation_generator(), CitationGenerator)

    def test_get_sentiment_analyzer(self):
        assert isinstance(get_sentiment_analyzer(), SentimentAnalyzer)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])