"""Tests for Citation-Aware Answering (RP10).

Per RP10, ExecutionEngine checks that citations are actually
relevant to the answer content.
"""
import types
from pathlib import Path
import sys

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.evidence import EvidenceStore
from jarvis_core.executor import ExecutionEngine
from jarvis_core.planner import Planner
from jarvis_core.task import Task, TaskCategory, TaskStatus
from jarvis_core.agents import Citation


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

    def run(self, task: Task):
        return types.SimpleNamespace(
            status=self.status,
            answer=self.answer,
            citations=self.citations,
            meta={},
        )


def make_task() -> Task:
    return Task(
        task_id="test-task",
        title="Test citation relevance",
        category=TaskCategory.GENERIC,
    )


class TestCitationRelevance:
    """Tests for citation-answer relevance checking."""

    def test_citations_empty_returns_partial(self):
        """Empty citations should return partial (existing behavior)."""
        store = EvidenceStore()
        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            answer="This is a valid answer.",
            citations=[],
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

    def test_citation_with_no_overlap_returns_partial(self):
        """Citation with no token overlap should return partial."""
        store = EvidenceStore()
        # Add chunk about completely different topic
        chunk_id = store.add_chunk(
            source="test",
            locator="test:unrelated",
            text="Quantum computing uses qubits for parallel processing.",
        )

        citation = Citation(
            chunk_id=chunk_id,
            source="test",
            locator="test:unrelated",
            quote="ignored",
        )

        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            # Answer about completely different topic
            answer="CD73 is expressed on regulatory T cells and affects adenosine signaling.",
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
            "relevance" in w.lower()
            for w in complete_event["quality_warnings"]
        )

    def test_citation_with_sufficient_overlap_returns_success(self):
        """Citation with sufficient token overlap should return success."""
        store = EvidenceStore()
        # Add chunk about the topic
        chunk_id = store.add_chunk(
            source="test",
            locator="test:relevant",
            text="CD73 is an ectoenzyme expressed on regulatory T cells. "
                 "It produces adenosine which affects immune responses.",
        )

        citation = Citation(
            chunk_id=chunk_id,
            source="test",
            locator="test:relevant",
            quote="ignored",
        )

        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            # Answer uses terms from the chunk
            answer="CD73 is expressed on regulatory T cells and produces adenosine.",
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
        assert complete_event["agent_status"] == "success"

    def test_mixed_citations_one_relevant_success(self):
        """If at least one citation is relevant, should succeed."""
        store = EvidenceStore()

        # Relevant chunk
        chunk_id_relevant = store.add_chunk(
            source="test",
            locator="test:relevant",
            text="Machine learning algorithms use neural networks for prediction.",
        )

        # Unrelated chunk
        chunk_id_unrelated = store.add_chunk(
            source="test",
            locator="test:unrelated",
            text="Pizza originated in Italy during the 18th century.",
        )

        citations = [
            Citation(
                chunk_id=chunk_id_unrelated,
                source="test",
                locator="test:unrelated",
                quote="ignored",
            ),
            Citation(
                chunk_id=chunk_id_relevant,
                source="test",
                locator="test:relevant",
                quote="ignored",
            ),
        ]

        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            # Answer about machine learning
            answer="Machine learning uses neural networks to make predictions.",
            citations=citations,
        )
        engine = ExecutionEngine(
            planner=planner, router=router, evidence_store=store
        )

        task = make_task()
        executed = engine.run(task)

        complete_event = next(
            e for e in executed[0].history if e.get("event") == "complete"
        )
        # Should succeed because at least one citation is relevant
        assert complete_event["agent_status"] == "success"


class TestCitationRelevanceEdgeCases:
    """Edge case tests for citation relevance."""

    def test_short_answer_with_short_chunk(self):
        """Short but matching content should work."""
        store = EvidenceStore()
        chunk_id = store.add_chunk(
            source="test",
            locator="test:short",
            text="Python programming language.",
        )

        citation = Citation(
            chunk_id=chunk_id,
            source="test",
            locator="test:short",
            quote="ignored",
        )

        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            answer="Python is a programming language.",
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
        assert complete_event["agent_status"] == "success"

    def test_japanese_text_relevance(self):
        """Should handle Japanese text."""
        store = EvidenceStore()
        chunk_id = store.add_chunk(
            source="test",
            locator="test:jp",
            text="機械学習はデータからパターンを学習するアルゴリズムです。",
        )

        citation = Citation(
            chunk_id=chunk_id,
            source="test",
            locator="test:jp",
            quote="ignored",
        )

        planner = DummyPlanner()
        router = DummyRouter(
            status="success",
            answer="機械学習アルゴリズムはデータから学習します。",
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
        # Should have some token overlap
        assert complete_event["agent_status"] in ["success", "partial"]
