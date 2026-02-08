"""TD-019 WebSocket contract tests for run progress."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import jarvis_web.app as app_module

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


def _prepare_run(tmp_path: Path) -> None:
    run_dir = tmp_path / "data" / "runs" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "result.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")
    (run_dir / "eval_summary.json").write_text("{}", encoding="utf-8")


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    if TestClient is None or app_module.app is None:
        pytest.skip("FastAPI not available")
    monkeypatch.chdir(tmp_path)
    _prepare_run(tmp_path)
    return TestClient(app_module.app)


def test_ws_runs_connect_and_receive_initial_events(client: TestClient) -> None:
    with client.websocket_connect("/ws/runs/run-1") as websocket:
        connected = websocket.receive_json()
        assert connected["event"] == "connected"
        assert connected["data"]["run_id"] == "run-1"

        status = websocket.receive_json()
        assert status["event"] == "run_status"
        assert status["data"]["run_id"] == "run-1"
        assert status["data"]["status"] == "running"


def test_ws_runs_ping_pong_and_disconnect(client: TestClient) -> None:
    with client.websocket_connect("/ws/runs/run-1") as websocket:
        websocket.receive_json()
        websocket.receive_json()
        websocket.send_text("ping")
        pong = websocket.receive_json()
        assert pong["event"] == "pong"
        assert pong["data"]["run_id"] == "run-1"
