"""Tests for summarize.summarizers module."""

from jarvis_core.summarize.summarizers import (
    SummaryOutput,
    Summarizer,
    generate_summaries,
)


class TestSummaryOutput:
    def test_to_dict(self):
        output = SummaryOutput(
            summary_300="Short summary",
            summary_detailed="Detailed summary",
            notebooklm_script="Script",
            metadata={"key": "value"},
        )
        d = output.to_dict()
        
        assert d["summary_300"] == "Short summary"
        assert d["summary_detailed"] == "Detailed summary"
        assert d["notebooklm_script"] == "Script"
        assert d["metadata"] == {"key": "value"}


class TestSummarizer:
    def test_init_without_llm(self):
        summarizer = Summarizer()
        assert summarizer is not None

    def test_generate_all_without_llm(self):
        summarizer = Summarizer()
        claims = [{"text": "Claim 1", "score": 0.9}]
        evidence = [{"text": "Evidence 1"}]
        
        result = summarizer.generate_all("test topic", claims, evidence)
        
        assert isinstance(result, SummaryOutput)
        assert len(result.summary_300) > 0
        assert len(result.summary_detailed) > 0
        assert len(result.notebooklm_script) > 0

    def test_generate_300(self):
        summarizer = Summarizer()
        result = summarizer.generate_300("ML topic", "Claim: AI is advancing.")
        
        assert len(result) > 0
        assert "ML topic" in result or "AI" in result

    def test_generate_detailed(self):
        summarizer = Summarizer()
        result = summarizer.generate_detailed("Test", "Claim text")
        
        assert len(result) > 0

    def test_generate_notebooklm(self):
        summarizer = Summarizer()
        result = summarizer.generate_notebooklm("Research", "Claims here")
        
        assert len(result) > 0

    def test_format_claims_with_evidence(self):
        summarizer = Summarizer()
        claims = [{"text": "Claim A", "score": 0.9}]
        evidence = [{"text": "Evidence for A"}]
        
        result = summarizer._format_claims_with_evidence(claims, evidence)
        
        assert "Claim A" in result or len(result) > 0


class TestGenerateSummaries:
    def test_generate_summaries_function(self):
        claims = [{"text": "Test claim"}]
        evidence = [{"text": "Test evidence"}]
        
        result = generate_summaries("topic", claims, evidence)
        
        assert isinstance(result, SummaryOutput)
