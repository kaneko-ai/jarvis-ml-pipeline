"""TD-019 API endpoint contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import jarvis_web.app as app_module

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


def _prepare_runs(tmp_path: Path) -> None:
    run_dir = tmp_path / "data" / "runs" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "result.json").write_text(
        json.dumps({"status": "success", "timestamp": "2026-02-08T00:00:00+00:00"}),
        encoding="utf-8",
    )
    (run_dir / "eval_summary.json").write_text(
        json.dumps({"metrics": {"score": 1.0}}), encoding="utf-8"
    )
    (run_dir / "report.md").write_text("# report", encoding="utf-8")
    (run_dir / "input.json").write_text("{}", encoding="utf-8")


def _assert_envelope(payload: dict) -> None:
    assert "status" in payload
    assert "data" in payload
    assert "errors" in payload
    assert isinstance(payload["errors"], list)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    if TestClient is None or app_module.app is None:
        pytest.skip("FastAPI not available")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JARVIS_WEB_TOKEN", raising=False)
    _prepare_runs(tmp_path)
    return TestClient(app_module.app)


def test_health_endpoint_contract(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "ok"
    assert payload["data"]["version"] == "1.0.0"
    assert "timestamp" in payload


def test_runs_list_endpoint_contract(client: TestClient) -> None:
    response = client.get("/api/runs")
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    assert "runs" in payload
    assert "total" in payload
    assert payload["data"]["total"] == payload["total"]


def test_run_detail_endpoint_contract(client: TestClient) -> None:
    response = client.get("/api/runs/run-1")
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    assert payload["run_id"] == "run-1"
    assert payload["data"]["run_id"] == "run-1"


def test_run_detail_not_found_returns_404_envelope(client: TestClient) -> None:
    response = client.get("/api/runs/does-not-exist")
    assert response.status_code == 404
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "error"


class _SearchResult:
    def to_dict(self) -> dict:
        return {"results": [{"id": "p1"}], "total": 1, "query": "demo"}


class _FakeSearchEngine:
    _loaded = True

    def search(self, q: str, top_k: int = 20, filters=None) -> _SearchResult:  # noqa: ANN001
        return _SearchResult()


def test_search_endpoint_contract(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jarvis_core.search.get_search_engine", lambda: _FakeSearchEngine())
    response = client.get("/api/search", params={"q": "demo", "top_k": 1})
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    assert "results" in payload
    assert payload["data"]["total"] == 1


def test_search_endpoint_empty_query_returns_400(client: TestClient) -> None:
    response = client.get("/api/search", params={"q": "  "})
    assert response.status_code == 400
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "error"


def test_upload_pdf_endpoint_contract_and_validation(client: TestClient) -> None:
    ok_response = client.post(
        "/api/upload/pdf",
        files=[("files", ("paper.pdf", b"%PDF-1.4 test", "application/pdf"))],
    )
    assert ok_response.status_code == 200
    ok_payload = ok_response.json()
    _assert_envelope(ok_payload)
    assert ok_payload["accepted"] == 1

    bad_response = client.post(
        "/api/upload/pdf",
        files=[("files", ("not_pdf.txt", b"text", "text/plain"))],
    )
    assert bad_response.status_code == 400
    bad_payload = bad_response.json()
    _assert_envelope(bad_payload)
    assert bad_payload["status"] == "error"


def test_kpi_endpoint_contract(client: TestClient) -> None:
    response = client.get("/api/kpi")
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    assert "definitions" in payload
    assert "current_values" in payload
