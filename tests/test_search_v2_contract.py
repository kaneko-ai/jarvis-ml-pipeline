from jarvis_core.retrieval.indexer import RetrievalIndexer
import importlib
import shutil
from pathlib import Path

import pytest


@pytest.fixture()
def indexed_env(tmp_path, monkeypatch):
    fixtures = Path("tests/retrieval/fixtures")
    data_dir = tmp_path / "data"
    kb_dir = data_dir / "kb" / "notes"
    runs_dir = data_dir / "runs"
    shutil.copytree(fixtures / "kb", kb_dir)
    shutil.copytree(fixtures / "runs", runs_dir)
    index_dir = data_dir / "index" / "v2"
    indexer = RetrievalIndexer(index_dir=index_dir, kb_dir=kb_dir, runs_dir=runs_dir)
    indexer.rebuild()
    monkeypatch.chdir(tmp_path)
    return tmp_path

def test_search_v2_contract(indexed_env, monkeypatch):
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("FastAPI not available")

    import jarvis_web.app as web_app

    importlib.reload(web_app)

    client = TestClient(web_app.create_app())
    payload = {
        "query": "CD73 adenosine",
        "mode": "hybrid",
        "top_k": 5,
        "filters": {"source_type_in": ["kb_topic", "claim", "run_report", "kb_paper"]},
    }
    response = client.post("/api/search/v2", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    for item in data["results"]:
        assert "provenance" in item
        assert item["provenance"].get("run_id") or item["provenance"].get("file_path")
