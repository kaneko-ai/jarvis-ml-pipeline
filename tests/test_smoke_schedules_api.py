import pytest

try:
    from fastapi.testclient import TestClient  # noqa: E402
    from jarvis_web import jobs  # noqa: E402
    from jarvis_web.app import app  # noqa: E402

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    TestClient = None
    jobs = None
    app = None

fastapi = pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi not installed")


@fastapi
def test_schedules_api_smoke(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_MODE", "disabled")
    from jarvis_web.config import reset_config

    reset_config()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(jobs, "run_in_background", lambda job_id, fn: None)

    client = TestClient(app)
    payload = {
        "name": "CD73 weekly",
        "timezone": "UTC",
        "rrule": "FREQ=WEEKLY;BYDAY=MO;BYHOUR=3;BYMINUTE=0;BYSECOND=0",
        "query": {"keywords": ["CD73"], "date_range_days": 30, "oa_only": True, "max_papers": 10},
        "outputs": {
            "generate_notes": True,
            "generate_package_zip": True,
            "generate_submission_package": False,
        },
        "limits": {
            "max_runtime_minutes": 60,
            "max_retries": 1,
            "cooldown_minutes_after_failure": 10,
        },
    }

    response = client.post("/api/schedules", json=payload)
    assert response.status_code == 200
    schedule = response.json()
    schedule_id = schedule["schedule_id"]

    list_response = client.get("/api/schedules")
    assert list_response.status_code == 200
    assert list_response.json()["schedules"]

    run_response = client.post(f"/api/schedules/{schedule_id}/run?force=true")
    assert run_response.status_code == 200

    history_response = client.get(f"/api/schedules/{schedule_id}/history")
    assert history_response.status_code == 200
    assert "history" in history_response.json()
