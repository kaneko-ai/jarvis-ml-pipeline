from jarvis_core.retrieval.hybrid_search import HybridSearchEngine
from jarvis_core.retrieval.indexer import RetrievalIndexer
import shutil
from pathlib import Path


def test_hybrid_ranking_returns_kb_topic(tmp_path):
    fixtures = Path("tests/retrieval/fixtures")
    data_dir = tmp_path / "data"
    kb_dir = data_dir / "kb" / "notes"
    runs_dir = data_dir / "runs"
    shutil.copytree(fixtures / "kb", kb_dir)
    shutil.copytree(fixtures / "runs", runs_dir)

    index_dir = data_dir / "index" / "v2"
    indexer = RetrievalIndexer(index_dir=index_dir, kb_dir=kb_dir, runs_dir=runs_dir)
    indexer.rebuild()

    engine = HybridSearchEngine(index_dir=index_dir)
    result = engine.search(query="CD73 adenosine", top_k=5, mode="hybrid")
    doc_ids = [item.chunk.doc_id for item in result.results]
    assert any(doc_id.startswith("kb:topic:CD73") for doc_id in doc_ids)