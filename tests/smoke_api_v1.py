import json

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("fastapi.testclient")

    from fastapi.testclient import TestClient

    from jarvis_web import app as app_module

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(app_module, "RUNS_DIR", runs_dir)
    monkeypatch.setattr(app_module, "LEGACY_RUNS_DIR", legacy_dir)

    run_dir = runs_dir / "run-123"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "result.json").write_text(json.dumps({"status": "success"}), encoding="utf-8")
    (run_dir / "eval_summary.json").write_text(
        json.dumps({"metrics": {"kpi": 1}}), encoding="utf-8"
    )
    (run_dir / "progress.json").write_text(
        json.dumps({"step": "done", "percent": 100, "counts": {"items": 1}}),
        encoding="utf-8",
    )
    (run_dir / "warnings.jsonl").write_text(
        json.dumps({"warning": "none"}) + "\n", encoding="utf-8"
    )
    (run_dir / "errors.jsonl").write_text("", encoding="utf-8")
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "sample.txt").write_text("hello", encoding="utf-8")

    return TestClient(app_module.app)


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_capabilities(client):
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v1"
    assert "features" in payload


def test_runs_list(client):
    response = client.get("/api/runs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["runs"][0]["run_id"] == "run-123"


def test_run_detail_and_files(client):
    response = client.get("/api/runs/run-123")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert any(entry["path"] == "artifacts/sample.txt" for entry in payload["files"])

    list_response = client.get("/api/runs/run-123/files")
    assert list_response.status_code == 200
    files_payload = list_response.json()
    assert any(entry["path"] == "artifacts/sample.txt" for entry in files_payload["files"])

    download = client.get("/api/runs/run-123/files/artifacts/sample.txt")
    assert download.status_code == 200


def test_unimplemented_endpoints(client):
    response = client.get("/api/qa/report")
    assert response.status_code == 501
    response = client.post("/api/submission/build")
    assert response.status_code == 501
    response = client.get("/api/feedback/risk")
    assert response.status_code == 501
    response = client.post("/api/decision/simulate")
    assert response.status_code == 501
