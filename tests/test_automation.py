"""Tests for workflow.automation module."""

from jarvis_core.workflow.automation import (
    TaskStatus,
    PipelineTask,
    PaperPipelineOrchestrator,
    WeeklyDigestGenerator,
    ResearchJournalBot,
    MeetingNotesGenerator,
    EmailDraftAssistant,
)


class TestTaskStatus:
    def test_values(self):
        # Enum comparison with .value
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestPipelineTask:
    def test_creation(self):
        task = PipelineTask(
            id="task-1",
            name="Data Loading",
            handler="load_data",
        )
        
        assert task.id == "task-1"
        assert task.status == TaskStatus.PENDING

    def test_with_dependencies(self):
        task = PipelineTask(
            id="task-2",
            name="Processing",
            handler="process",
            dependencies=["task-1"],
        )
        
        assert "task-1" in task.dependencies


class TestPaperPipelineOrchestrator:
    def test_init(self):
        orchestrator = PaperPipelineOrchestrator()
        
        assert orchestrator.tasks == {}
        assert orchestrator.execution_order == []

    def test_add_task(self):
        orchestrator = PaperPipelineOrchestrator()
        task = PipelineTask(id="t1", name="Task 1", handler="handler1")
        
        orchestrator.add_task(task)
        
        assert "t1" in orchestrator.tasks

    def test_register_handler(self):
        orchestrator = PaperPipelineOrchestrator()
        
        def dummy_handler(context):
            return {"result": "done"}
        
        orchestrator.register_handler("handler1", dummy_handler)
        
        assert "handler1" in orchestrator.handlers


class TestWeeklyDigestGenerator:
    def test_init(self):
        generator = WeeklyDigestGenerator()
        
        assert generator.topics == []
        assert generator.papers == []

    def test_set_interests(self):
        generator = WeeklyDigestGenerator()
        
        generator.set_interests(["cancer", "immunotherapy"])
        
        assert "cancer" in generator.topics

    def test_add_papers(self):
        generator = WeeklyDigestGenerator()
        papers = [
            {"title": "Paper 1", "abstract": "About cancer"},
            {"title": "Paper 2", "abstract": "About treatment"},
        ]
        
        generator.add_papers(papers)
        
        assert len(generator.papers) == 2

    def test_generate_returns_dict(self):
        generator = WeeklyDigestGenerator()
        
        digest = generator.generate()
        
        # Check it returns a dict with relevant keys
        assert isinstance(digest, dict)
        assert "week_of" in digest or "papers" in digest or "trends" in digest


class TestResearchJournalBot:
    def test_init(self):
        bot = ResearchJournalBot()
        assert bot.entries == []

    def test_log_activity(self):
        bot = ResearchJournalBot()
        
        bot.log_activity("read_paper", {"title": "Paper 1"})
        
        assert len(bot.entries) == 1

    def test_generate_daily_log_returns_string_or_dict(self):
        bot = ResearchJournalBot()
        bot.log_activity("read_paper", {"title": "Paper 1"})
        
        log = bot.generate_daily_log()
        
        # May return string or dict
        assert isinstance(log, (str, dict))


class TestMeetingNotesGenerator:
    def test_process_empty(self):
        generator = MeetingNotesGenerator()
        
        notes = generator.process("")
        
        assert "summary" in notes or isinstance(notes, dict)

    def test_process_transcript(self):
        generator = MeetingNotesGenerator()
        transcript = "Alice: Let's discuss the project. Bob: I agree we need more data."
        
        notes = generator.process(transcript)
        
        assert isinstance(notes, dict)


class TestEmailDraftAssistant:
    def test_templates_exist(self):
        assert "collaboration" in EmailDraftAssistant.TEMPLATES
        assert "review_response" in EmailDraftAssistant.TEMPLATES

    def test_generate_collaboration(self):
        assistant = EmailDraftAssistant()
        
        draft = assistant.generate("collaboration", {"name": "Dr. Smith", "field": "oncology"})
        
        assert isinstance(draft, str)

    def test_generate_unknown_template(self):
        assistant = EmailDraftAssistant()
        
        draft = assistant.generate("unknown_type", {})
        
        # Should handle gracefully
        assert isinstance(draft, str)
