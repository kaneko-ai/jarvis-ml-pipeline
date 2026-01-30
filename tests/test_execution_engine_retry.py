from jarvis_core.executor import ExecutionEngine
from jarvis_core.planner import Planner
from jarvis_core.retry import RetryPolicy
from jarvis_core.task import Task, TaskCategory, TaskPriority, TaskStatus
from jarvis_core.validation import EvaluationResult


class DummyResult:
    def __init__(self, answer: str):
        self.answer = answer
        self.meta = {"answer": answer}


class DummyPlanner(Planner):
    def __init__(self, subtasks):
        self._subtasks = subtasks

    def plan(self, task: Task):  # noqa: D401
        return self._subtasks


class DummyRouter:
    def __init__(self, results):
        self._results = results
        self.calls = 0

    def run(self, task: Task):  # noqa: D401
        result = self._results[self.calls]
        self.calls += 1
        return result


def validator_for_success(result):
    ok = getattr(result, "answer", "") == "good"
    return EvaluationResult(ok=ok, errors=[] if ok else ["bad_answer"])


def make_task(task_id: str) -> Task:
    return Task(
        task_id=task_id,
        title="do something",
        category=TaskCategory.GENERIC,
        inputs={},
        constraints={},
        priority=TaskPriority.NORMAL,
    )


def test_execution_engine_retries_until_success():
    task = make_task("t1")
    planner = DummyPlanner([task])
    router = DummyRouter([DummyResult("bad"), DummyResult("good")])
    policy = RetryPolicy(max_attempts=2)

    engine = ExecutionEngine(planner, router, retry_policy=policy, validator=validator_for_success)
    executed = engine.run(task)

    assert router.calls == 2
    assert executed[0].status == TaskStatus.DONE
    assert executed[0].history[-1]["attempts"] == 2


def test_execution_engine_stops_after_max_attempts():
    task = make_task("t2")
    planner = DummyPlanner([task])
    router = DummyRouter([DummyResult("bad")])
    policy = RetryPolicy(max_attempts=1)

    engine = ExecutionEngine(planner, router, retry_policy=policy, validator=validator_for_success)
    executed = engine.run(task)

    assert router.calls == 1
    assert executed[0].status == TaskStatus.FAILED


def test_execution_engine_without_validator_runs_once():
    task = make_task("t3")
    planner = DummyPlanner([task])
    router = DummyRouter([DummyResult("any")])

    engine = ExecutionEngine(planner, router)
    executed = engine.run(task)

    assert router.calls == 1
    assert executed[0].status == TaskStatus.DONE
    assert executed[0].history[-1]["attempts"] == 1