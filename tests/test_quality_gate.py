"""Tests for AgentResult quality gate in ExecutionEngine.

Per JARVIS_MASTER.md Section 5.4.1 and 5.4.2, the ExecutionEngine
is the final arbiter of AgentResult status.

Note: Citations are now validated against EvidenceStore.
"""
import sys
import types
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.agents import Citation
from jarvis_core.evidence import EvidenceStore
from jarvis_core.executor import ExecutionEngine
from jarvis_core.planner import Planner
from jarvis_core.task import Task, TaskCategory, TaskStatus


class DummyPlanner(Planner):
    """Planner that returns the task itself as the only subtask."""

    def plan(self, task: Task):
        return [task]


class DummyRouter:
    """Router that returns a configurable AgentResult-like object."""

    def __init__(
        self,
        status: str = "success",
        answer: str = "test answer",
        citations: list | None = None,
    ):
        self.status = status
        self.answer = answer
        self.citations = citations if citations is not None else []
        self.calls = []

    def run(self, task: Task):
        self.calls.append(task)
        return types.SimpleNamespace(
            status=self.status,
            answer=self.answer,
            citations=self.citations,
            meta={},
        )


def make_task() -> Task:
    return Task(
        task_id="test-task",
        title="Test quality gate",
        category=TaskCategory.GENERIC,
    )


def make_evidence_store_with_chunk() -> tuple[EvidenceStore, str]:
    """Create an EvidenceStore with a valid chunk and return both.

    Note: The chunk text must overlap with test answer texts to pass
    RP10 citation-relevance checks.
    """
    store = EvidenceStore()
    chunk_id = store.add_chunk(
        source="test_source.pdf",
        locator="page:5",
        # Text that overlaps with typical test answers
        text="CD73 is expressed on regulatory T cells and affects adenosine signaling. "
             "This is valid answer content for testing quality gates.",
    )
    return store, chunk_id


class TestQualityGateEmptyAnswer:
    """Test case 1: answer empty -> status=fail"""

    def test_empty_answer_returns_fail(self):
        """Verify empty answer results in status=fail."""
        planner = DummyPlanner()
        router = DummyRouter(status="success", answer="", citations=[])
        engine = ExecutionEngine(planner=planner, router=router)

        task = make_task()
        executed = engine.run(task)

        assert len(executed) == 1
        assert executed[0].status == TaskStatus.FAILED
        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        assert complete_event["agent_status"] == "fail"
        assert "empty_answer" in complete_event["quality_warnings"]

    def test_whitespace_only_answer_returns_fail(self):
        """Verify whitespace-only answer results in status=fail."""
        planner = DummyPlanner()
        router = DummyRouter(status="success", answer="   \n\t  ", citations=[])
        engine = ExecutionEngine(planner=planner, router=router)

        task = make_task()
        executed = engine.run(task)

        assert executed[0].status == TaskStatus.FAILED
        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        assert complete_event["agent_status"] == "fail"


class TestQualityGateNoCitations:
    """Test case 2: answer present, no citations -> status=partial"""

    def test_no_citations_returns_partial(self):
        """Verify answer without citations results in status=partial."""
        planner = DummyPlanner()
        router = DummyRouter(
            status="success", answer="This is a valid answer", citations=[]
        )
        engine = ExecutionEngine(planner=planner, router=router)

        task = make_task()
        executed = engine.run(task)

        assert len(executed) == 1
        # partial does not fail the task, but status is downgraded
        assert executed[0].status == TaskStatus.DONE
        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        assert complete_event["agent_status"] == "partial"
        assert "no_valid_citations" in complete_event["quality_warnings"]


class TestQualityGateValidCitations:
    """Test case 3: answer + valid citations -> status=success"""

    def test_valid_citations_returns_success(self):
        """Verify answer with valid citations results in status=success."""
        store, chunk_id = make_evidence_store_with_chunk()
        citation = Citation(
            chunk_id=chunk_id,
            source="ignored",
            locator="ignored",
            quote="ignored",
        )

        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            answer="CD73 is expressed on regulatory T cells.",
            citations=[citation],
        )
        engine = ExecutionEngine(
            planner=planner, router=router, evidence_store=store
        )

        task = make_task()
        executed = engine.run(task)

        assert len(executed) == 1
        assert executed[0].status == TaskStatus.DONE
        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        assert complete_event["agent_status"] == "success"
        assert complete_event["quality_warnings"] is None or \
            len(complete_event["quality_warnings"]) == 0


class TestQualityGateInvalidCitations:
    """Test case 4: citation with missing/invalid chunk_id -> status=partial"""

    def test_citation_missing_chunk_id_returns_partial(self):
        """Verify citation with empty chunk_id results in status=partial."""
        planner = DummyPlanner()
        invalid_citation = Citation(
            chunk_id="",  # Empty chunk_id
            source="test.pdf",
            locator="page:1",
            quote="quote",
        )
        router = DummyRouter(
            status="success",
            answer="This is a test answer",
            citations=[invalid_citation],
        )
        engine = ExecutionEngine(planner=planner, router=router)

        task = make_task()
        executed = engine.run(task)

        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        assert complete_event["agent_status"] == "partial"
        assert any("chunk_id" in w for w in complete_event["quality_warnings"])

    def test_citation_nonexistent_chunk_returns_partial(self):
        """Verify citation referencing nonexistent chunk returns partial."""
        store = EvidenceStore()  # Empty store
        citation = Citation(
            chunk_id="nonexistent-chunk-id",
            source="test.pdf",
            locator="page:1",
            quote="quote",
        )
        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            answer="This is a test answer",
            citations=[citation],
        )
        engine = ExecutionEngine(
            planner=planner, router=router, evidence_store=store
        )

        task = make_task()
        executed = engine.run(task)

        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        assert complete_event["agent_status"] == "partial"
        assert any(
            "not_in_evidence_store" in w
            for w in complete_event["quality_warnings"]
        )

    def test_mixed_valid_invalid_citations(self):
        """Verify mix of valid and invalid citations uses valid ones."""
        store, chunk_id = make_evidence_store_with_chunk()
        valid_citation = Citation(
            chunk_id=chunk_id,
            source="ignored",
            locator="ignored",
            quote="ignored",
        )
        invalid_citation = Citation(
            chunk_id="",  # Invalid
            source="",
            locator="",
            quote="",
        )

        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            answer="This is valid answer content for testing.",
            citations=[invalid_citation, valid_citation],
        )
        engine = ExecutionEngine(
            planner=planner, router=router, evidence_store=store
        )

        task = make_task()
        executed = engine.run(task)

        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        # Should be success because we have at least one valid citation
        assert complete_event["agent_status"] == "success"
        # But should have warning about the invalid one
        assert any("chunk_id" in w for w in complete_event["quality_warnings"])


class TestAgentStatusOverride:
    """Test that ExecutionEngine overrides agent-provided status."""

    def test_agent_fail_with_valid_output_becomes_partial(self):
        """Verify agent fail with valid output becomes partial."""
        store, chunk_id = make_evidence_store_with_chunk()
        citation = Citation(
            chunk_id=chunk_id,
            source="ignored",
            locator="ignored",
            quote="ignored",
        )

        planner = DummyPlanner()
        router = DummyRouter(
            status="fail",  # Agent says fail
            answer="But this answer is valid content for testing.",
            citations=[citation],
        )
        engine = ExecutionEngine(
            planner=planner, router=router, evidence_store=store
        )

        task = make_task()
        executed = engine.run(task)

        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        # Should be partial, not fail
        assert complete_event["agent_status"] == "partial"
        assert "agent_reported_fail_but_output_valid" in complete_event["quality_warnings"]

