from jarvis_core.retrieval.indexer import RetrievalIndexer
import shutil
from pathlib import Path


def test_index_incremental(tmp_path):
    fixtures = Path("tests/retrieval/fixtures")
    data_dir = tmp_path / "data"
    kb_dir = data_dir / "kb" / "notes"
    runs_dir = data_dir / "runs"
    shutil.copytree(fixtures / "kb", kb_dir)
    shutil.copytree(fixtures / "runs" / "RUN_1", runs_dir / "RUN_1")

    index_dir = data_dir / "index" / "v2"
    indexer = RetrievalIndexer(index_dir=index_dir, kb_dir=kb_dir, runs_dir=runs_dir)
    manifest = indexer.rebuild()
    assert manifest.chunks > 0

    shutil.copytree(fixtures / "runs" / "RUN_2", runs_dir / "RUN_2")
    manifest_updated = indexer.update()
    assert manifest_updated.chunks >= manifest.chunks
    assert "RUN_2" in manifest_updated.indexed_runs