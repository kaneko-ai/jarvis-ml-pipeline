from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.agents.literature import LiteratureSurveyAgent, PaperSummary, run_literature_survey  # noqa: E402
from jarvis_core.agents import AgentResult  # noqa: E402
from jarvis_core.task import Task, TaskCategory  # noqa: E402


def test_run_literature_survey_formats_markdown(monkeypatch):
    monkeypatch.setattr(
        "jarvis_core.agents.literature.search_pubmed",
        lambda query, max_results=20: ["1", "2"],
    )
    monkeypatch.setattr(
        "jarvis_core.agents.literature.fetch_pubmed_details",
        lambda pmids: [
            PaperSummary(
                pmid="1",
                title="Title One",
                journal="Journal A",
                year=2024,
                doi="10.1/one",
                url="http://example.com/1",
                abstract="Abstract one",
            ),
            PaperSummary(
                pmid="2",
                title="Title Two",
                journal="Journal B",
                year=2023,
                doi=None,
                url=None,
                abstract=None,
            ),
        ],
    )

    task = Task(
        id="lit1",
        category=TaskCategory.LITERATURE_REVIEW,
        goal="Find kinase papers",
        inputs={"query": "kinase"},
    )

    result = run_literature_survey(task, config={"default_max_results": 5})
    assert "Literature Survey for`" not in result.answer  # spacing check
    assert "Literature Survey for `kinase`" in result.answer
    assert len(result.meta["papers"]) == 2
    assert "Title One" in result.answer
    assert result.meta["papers"][0]["pmid"] == "1"


def test_literature_agent_run_task_invokes_helper(monkeypatch):
    calls = {}

    def fake_run(task, config=None):  # noqa: ANN001
        calls["called"] = True
        return AgentResult(thought="", answer="ok", meta={"papers": []})

    monkeypatch.setattr("jarvis_core.agents.literature.run_literature_survey", fake_run)

    agent = LiteratureSurveyAgent()
    task = Task(id="lit2", category=TaskCategory.LITERATURE_REVIEW, goal="Test", inputs={})
    result = agent.run_task(task)

    assert calls.get("called") is True
    assert result.answer == "ok"
