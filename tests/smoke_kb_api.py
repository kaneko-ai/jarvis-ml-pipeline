import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    pytest.importorskip("fastapi.testclient")

    from fastapi.testclient import TestClient

    from jarvis_web import app as app_module
    from jarvis_web.routes import kb as kb_routes
    from jarvis_web.routes import packs as packs_routes

    kb_root = tmp_path / "kb"
    packs_root = tmp_path / "packs"
    (kb_root / "notes" / "papers").mkdir(parents=True, exist_ok=True)
    (kb_root / "notes" / "topics").mkdir(parents=True, exist_ok=True)

    (kb_root / "notes" / "papers" / "PMID_1.md").write_text("paper", encoding="utf-8")
    (kb_root / "notes" / "topics" / "cd73.md").write_text("topic", encoding="utf-8")
    (kb_root / "index.json").write_text(
        '{"papers": {"1": {"updated_at": "2024-01-01T00:00:00+00:00"}}, "topics": {"cd73": {"updated_at": "2024-01-02T00:00:00+00:00"}}, "runs": {}}',
        encoding="utf-8",
    )

    pack_dir = packs_root / "weekly" / "2024-01"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "weekly_pack.zip").write_bytes(b"zip")
    (pack_dir / "metadata.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(kb_routes, "KB_ROOT", kb_root)
    monkeypatch.setattr(packs_routes, "PACKS_ROOT", packs_root)

    return TestClient(app_module.app)


def test_kb_status(client):
    response = client.get("/api/kb/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["papers"] == 1
    assert "cd73" in payload["topic_list"]


def test_packs_list(client):
    response = client.get("/api/packs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["packs"]
