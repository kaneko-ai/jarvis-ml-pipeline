from __future__ import annotations
import io
import json
import re
import zipfile
from pathlib import Path
import pytest
import jarvis_web.app as jarvis_app_module


try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


ROOT = Path(__file__).resolve().parents[1]
API_MAP_PATH = ROOT / "jarvis_web" / "contracts" / "api_map_v1.json"

PARAM_VALUES = {
    "run_id": "smoke-run",
    "path": "result.json",
    "paper_id": "paper-1",
    "job_id": "job_smoke",
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    if TestClient is None or jarvis_app_module.app is None:
        pytest.skip("FastAPI not available")

    monkeypatch.chdir(tmp_path)
    _prepare_sample_data(tmp_path)
    return TestClient(jarvis_app_module.app)


def _prepare_sample_data(tmp_path: Path) -> None:
    run_dir = tmp_path / "logs" / "runs" / "smoke-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "result.json").write_text("{}", encoding="utf-8")
    (run_dir / "eval_summary.json").write_text("{}", encoding="utf-8")

    research_dir = tmp_path / "data" / "research" / "smoke-run"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (research_dir / "canonical_papers.jsonl").write_text(
        json.dumps({"canonical_paper_id": "paper-1", "title": "Demo"}) + "\n",
        encoding="utf-8",
    )
    (research_dir / "claims.jsonl").write_text(
        json.dumps({"paper_id": "paper-1", "claim_text": "demo"}) + "\n",
        encoding="utf-8",
    )

    jobs_dir = tmp_path / "data" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    (jobs_dir / "job_smoke.json").write_text(
        json.dumps({"job_id": "job_smoke", "status": "success"}),
        encoding="utf-8",
    )
    (jobs_dir / "job_smoke.events.jsonl").write_text(
        json.dumps({"timestamp": "now", "level": "info", "message": "ok"}) + "\n",
        encoding="utf-8",
    )


def _load_api_map() -> dict:
    return json.loads(API_MAP_PATH.read_text(encoding="utf-8"))


def _resolve_path(template: str) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return PARAM_VALUES.get(key, "sample")

    return re.sub(r"\{([^}]+)\}", replace, template)


def _zip_payload() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("sample.pdf", b"sample")
    return buffer.getvalue()


def test_api_map_vs_capabilities(client, monkeypatch):
    api_map = _load_api_map()
    response = client.get("/api/capabilities")
    assert response.status_code == 200

    payload = response.json()
    base_paths = api_map.get("base_paths", {})
    core_keys = {
        "capabilities",
        "health",
        "runs_list",
        "run_detail",
        "run_files",
        "run_file_get",
    }
    assert core_keys.issubset(base_paths.keys())

    endpoints = payload.get("endpoints", {})
    features = payload.get("features", {})

    assert set(endpoints.keys()).issubset(base_paths.keys())
    for key, enabled in features.items():
        if enabled:
            assert key in base_paths
            assert endpoints.get(key) == base_paths[key]

    monkeypatch.setenv("API_TOKEN", "smoke-token")

    request_map = {
        "health": {"method": "GET"},
        "capabilities": {"method": "GET"},
        "runs_list": {"method": "GET", "params": {"limit": 1}},
        "run_detail": {"method": "GET"},
        "run_file_get": {"method": "GET"},
        "run_manifest": {"method": "GET"},
        "research_rank": {"method": "GET", "params": {"run_id": "smoke-run", "top_k": 1}},
        "research_paper": {"method": "GET", "params": {"run_id": "smoke-run"}},
        "search": {"method": "GET", "params": {"q": "test", "top_k": 1}},
        "job_detail": {"method": "GET"},
        "job_events": {"method": "GET", "params": {"tail": 1}},
        "jobs": {
            "method": "POST",
            "json": {"type": "collect_and_ingest", "payload": {"query": "q"}},
        },
        "finance_simulate": {"method": "POST", "json": {"months": 1}},
        "finance_optimize": {"method": "POST", "json": {"months": 1}},
        "finance_download": {"method": "GET", "params": {"format": "zip"}},
        "upload_pdf": {
            "method": "POST",
            "files": {"files": ("sample.pdf", b"data", "application/pdf")},
        },
        "upload_bibtex": {
            "method": "POST",
            "files": {"files": ("sample.bib", b"@article{}", "text/plain")},
        },
        "upload_zip": {
            "method": "POST",
            "files": {"file": ("sample.zip", _zip_payload(), "application/zip")},
        },
    }

    for key, enabled in features.items():
        if key not in base_paths:
            continue
        path = _resolve_path(base_paths[key])
        method = api_map.get("methods", {}).get(key, "GET")
        request_data = request_map.get(key, {"method": method})

        response = client.request(
            request_data.get("method", method),
            path,
            params=request_data.get("params"),
            json=request_data.get("json"),
            files=request_data.get("files"),
        )

        if enabled:
            assert response.status_code in {200, 401}
        else:
            assert response.status_code == 501