"""Coverage tests for jarvis_core.orchestrator.agents.synthesis."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from async_test_utils import sync_async_test
from jarvis_core.orchestrator.agents.synthesis import (
    EvidenceSynthesisAgent,
    Paper,
    SynthesisReport,
)


class TestDataclasses:
    def test_paper(self) -> None:
        p = Paper(title="Test", abstract="abs", full_text="full")
        assert p.title == "Test"
        assert p.abstract == "abs"

    def test_paper_defaults(self) -> None:
        p = Paper(title="Test")
        assert p.abstract == ""
        assert p.full_text == ""

    def test_synthesis_report(self) -> None:
        r = SynthesisReport(summary="Sum")
        assert r.summary == "Sum"
        assert r.evidence_table == []
        assert r.contradictions == []
        assert r.gaps == []
        assert r.strength_of_evidence == "moderate"


class TestSynthesizeAgent:
    @sync_async_test
    async def test_no_papers(self) -> None:
        agent = EvidenceSynthesisAgent()
        report = await agent.synthesize([], "What is X?")
        assert "no papers found" in report.strength_of_evidence.lower()
        assert report.evidence_table == []

    @sync_async_test
    async def test_single_high_evidence_paper(self) -> None:
        agent = EvidenceSynthesisAgent()
        mock_grade = MagicMock()
        mock_grade.level.value = 1
        mock_grade.confidence = 0.9

        with patch("jarvis_core.orchestrator.agents.synthesis.grade_evidence", return_value=mock_grade):
            with patch("jarvis_core.orchestrator.agents.synthesis.ContradictionDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = []
                paper = Paper(title="RCT Study", abstract="Methods", full_text="Full text")
                report = await agent.synthesize([paper], "Effect of X")

        assert len(report.evidence_table) == 1
        assert report.evidence_table[0]["evidence_level"] == 1
        assert "high" in report.strength_of_evidence

    @sync_async_test
    async def test_multiple_low_evidence_papers(self) -> None:
        agent = EvidenceSynthesisAgent()
        mock_grade = MagicMock()
        mock_grade.level.value = 4
        mock_grade.confidence = 0.5

        with patch("jarvis_core.orchestrator.agents.synthesis.grade_evidence", return_value=mock_grade):
            with patch("jarvis_core.orchestrator.agents.synthesis.ContradictionDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = []
                papers = [Paper(title=f"Paper {i}") for i in range(4)]
                report = await agent.synthesize(papers, "Low evidence Q")

        assert "low" in report.strength_of_evidence
        assert len(report.evidence_table) == 4

    @sync_async_test
    async def test_moderate_evidence(self) -> None:
        agent = EvidenceSynthesisAgent()
        mock_grade = MagicMock()
        mock_grade.level.value = 2
        mock_grade.confidence = 0.7

        with patch("jarvis_core.orchestrator.agents.synthesis.grade_evidence", return_value=mock_grade):
            with patch("jarvis_core.orchestrator.agents.synthesis.ContradictionDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = []
                papers = [Paper(title=f"Paper {i}") for i in range(3)]
                report = await agent.synthesize(papers, "Moderate Q")

        assert "moderate" in report.strength_of_evidence

    @sync_async_test
    async def test_contradictions_downgrade(self) -> None:
        agent = EvidenceSynthesisAgent()
        mock_grade = MagicMock()
        mock_grade.level.value = 1
        mock_grade.confidence = 0.9

        mock_contradiction = MagicMock()
        mock_contradiction.statement_a = "A finds X"
        mock_contradiction.statement_b = "B finds not X"
        mock_contradiction.confidence = 0.8
        mock_contradiction.reason = "Opposing conclusions"

        with patch("jarvis_core.orchestrator.agents.synthesis.grade_evidence", return_value=mock_grade):
            with patch("jarvis_core.orchestrator.agents.synthesis.ContradictionDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = [mock_contradiction]
                papers = [Paper(title=f"P{i}") for i in range(3)]
                report = await agent.synthesize(papers, "Q?")

        assert "downgraded" in report.strength_of_evidence
        assert len(report.contradictions) == 1

    @sync_async_test
    async def test_gaps_few_papers(self) -> None:
        agent = EvidenceSynthesisAgent()
        mock_grade = MagicMock()
        mock_grade.level.value = 3
        mock_grade.confidence = 0.6

        with patch("jarvis_core.orchestrator.agents.synthesis.grade_evidence", return_value=mock_grade):
            with patch("jarvis_core.orchestrator.agents.synthesis.ContradictionDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = []
                papers = [Paper(title="Only one")]
                report = await agent.synthesize(papers, "Q?")

        assert len(report.gaps) >= 1
        assert any("Limited" in g for g in report.gaps)

    @sync_async_test
    async def test_gaps_no_high_level(self) -> None:
        agent = EvidenceSynthesisAgent()
        mock_grade = MagicMock()
        mock_grade.level.value = 4
        mock_grade.confidence = 0.4

        with patch("jarvis_core.orchestrator.agents.synthesis.grade_evidence", return_value=mock_grade):
            with patch("jarvis_core.orchestrator.agents.synthesis.ContradictionDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = []
                papers = [Paper(title=f"P{i}") for i in range(5)]
                report = await agent.synthesize(papers, "Q?")

        assert any("high-level" in g.lower() or "RCT" in g or "Systematic" in g for g in report.gaps)
