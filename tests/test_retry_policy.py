from jarvis_core.retry import RetryPolicy
from jarvis_core.validation import EvaluationResult


def test_retry_policy_allows_retry_until_max():
    policy = RetryPolicy(max_attempts=2)
    eval_fail = EvaluationResult(ok=False, errors=["x"])

    decision_first = policy.decide(eval_fail, attempt=1)
    decision_second = policy.decide(eval_fail, attempt=2)

    assert decision_first.should_retry is True
    assert decision_first.reason == "validation_failed"
    assert decision_second.should_retry is False
    assert decision_second.reason == "max_attempts_reached"


def test_retry_policy_no_retry_when_ok():
    policy = RetryPolicy(max_attempts=3)
    eval_ok = EvaluationResult(ok=True, errors=[])

    decision = policy.decide(eval_ok, attempt=1)

    assert decision.should_retry is False
    assert decision.reason is None
