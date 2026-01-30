from jarvis_core.ops.diagnostics import RunDiagnostics


def test_diagnostics_timeout():
    diag = RunDiagnostics()
    summary = {
        "run_id": "r1",
        "errors": ["Request to https://api.openai.com timed out (ReadTimeout)"],
    }

    res = diag.analyze(summary)
    assert res.error_type == "NetworkTimeout"
    assert res.is_recoverable
    assert "backoff" in res.suggested_action


def test_diagnostics_rate_limit():
    diag = RunDiagnostics()
    summary = {"run_id": "r2", "errors": ["429 Too Many Requests: You have exceeded your quota."]}

    res = diag.analyze(summary)
    assert res.error_type == "RateLimit"
    assert res.is_recoverable


def test_diagnostics_unrecoverable():
    diag = RunDiagnostics()
    summary = {"run_id": "r3", "errors": ["FileNotFoundError: /data/input.pdf"]}

    res = diag.analyze(summary)
    assert res.error_type == "MissingResource"
    assert not res.is_recoverable


def test_diagnostics_no_error():
    diag = RunDiagnostics()
    summary = {"run_id": "r4", "errors": []}

    res = diag.analyze(summary)
    assert res.error_type == "None"
