from __future__ import annotations

import pytest

import jarvis_web.app as jarvis_app_module


def test_obs_health_and_metrics_summary(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    if jarvis_app_module.app is None:
        pytest.skip("FastAPI not available")

    monkeypatch.chdir(tmp_path)
    client = pytest.importorskip("fastapi.testclient").TestClient(jarvis_app_module.app)

    health = client.get("/api/obs/health")
    assert health.status_code == 200
    assert health.json().get("status") == "ok"

    summary = client.get("/api/obs/metrics/summary")
    assert summary.status_code == 200
    assert "runs_total" in summary.json()
