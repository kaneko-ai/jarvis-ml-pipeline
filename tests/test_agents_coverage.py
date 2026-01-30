"""Tests for agents module - Coverage improvement (FIXED)."""


class TestCitation:
    """Tests for Citation dataclass."""

    def test_citation_creation(self):
        """Test Citation creation."""
        from jarvis_core.agents import Citation

        citation = Citation(
            chunk_id="chunk1",
            source="paper1.pdf",
            locator="page 5",
            quote="Test quote",
        )

        assert citation.chunk_id == "chunk1"
        assert citation.source == "paper1.pdf"
        assert citation.locator == "page 5"
        assert citation.quote == "Test quote"


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_agent_result_minimal(self):
        """Test AgentResult with minimal fields."""
        from jarvis_core.agents import AgentResult

        result = AgentResult(status="success", answer="Test answer")

        assert result.status == "success"
        assert result.answer == "Test answer"
        assert result.citations == []
        assert result.meta is None

    def test_agent_result_with_citations(self):
        """Test AgentResult with citations."""
        from jarvis_core.agents import AgentResult, Citation

        citations = [
            Citation(chunk_id="c1", source="s1", locator="l1", quote="q1"),
        ]

        result = AgentResult(
            status="success",
            answer="Answer with citations",
            citations=citations,
            meta={"key": "value"},
        )

        assert len(result.citations) == 1
        assert result.meta == {"key": "value"}


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_base_agent_name(self):
        """Test BaseAgent has name."""
        from jarvis_core.agents import BaseAgent

        agent = BaseAgent()
        assert agent.name == "base"

    def test_extract_answer(self):
        """Test _extract_answer static method."""
        from jarvis_core.agents import BaseAgent

        result = BaseAgent._extract_answer("Test text")
        assert result == "Test text"


class TestThesisAgent:
    """Tests for ThesisAgent class."""

    def test_thesis_agent_name(self):
        """Test ThesisAgent has correct name."""
        from jarvis_core.agents import ThesisAgent

        agent = ThesisAgent()
        assert agent.name == "thesis"


class TestESEditAgent:
    """Tests for ESEditAgent class."""

    def test_es_edit_agent_name(self):
        """Test ESEditAgent has correct name."""
        from jarvis_core.agents import ESEditAgent

        agent = ESEditAgent()
        assert agent.name == "es_edit"


class TestMiscAgent:
    """Tests for MiscAgent class."""

    def test_misc_agent_name(self):
        """Test MiscAgent has correct name."""
        from jarvis_core.agents import MiscAgent

        agent = MiscAgent()
        assert agent.name == "misc"


class TestPaperFetcherAgent:
    """Tests for PaperFetcherAgent class."""

    def test_paper_fetcher_agent_name(self):
        """Test PaperFetcherAgent has correct name."""
        from jarvis_core.agents import PaperFetcherAgent

        agent = PaperFetcherAgent()
        assert agent.name == "paper_fetcher"


class TestMyGPTPaperAnalyzerAgent:
    """Tests for MyGPTPaperAnalyzerAgent class."""

    def test_mygpt_paper_analyzer_agent_name(self):
        """Test MyGPTPaperAnalyzerAgent has correct name."""
        from jarvis_core.agents import MyGPTPaperAnalyzerAgent

        agent = MyGPTPaperAnalyzerAgent()
        assert agent.name == "mygpt_paper_analyzer"


class TestJobAssistantAgent:
    """Tests for JobAssistantAgent class."""

    def test_job_assistant_agent_name(self):
        """Test JobAssistantAgent has correct name."""
        from jarvis_core.agents import JobAssistantAgent

        agent = JobAssistantAgent()
        assert agent.name == "job_assistant"