"""
JARVIS Reproducibility Snapshot Tests

M2: 再現性完備のテスト
- スナップショット保存/読込
- 再実行での結果一致
- degradedフラグ
"""

from tempfile import TemporaryDirectory

import pytest

from jarvis_core.ops.snapshot import (
    ChunkMapping,
    ModelIO,
    QueryPackage,
    RetrievedContent,
    SearchResultItem,
    Snapshot,
    SnapshotManager,
)


class TestSnapshotCreation:
    """スナップショット作成テスト."""

    def test_query_package_hash(self):
        """QueryPackageのハッシュが決定的であること."""
        qp1 = QueryPackage(query="CD73 cancer", source="pubmed")
        qp2 = QueryPackage(query="CD73 cancer", source="pubmed")
        qp3 = QueryPackage(query="CD73 tumor", source="pubmed")

        assert qp1.query_hash == qp2.query_hash
        assert qp1.query_hash != qp3.query_hash

    def test_snapshot_to_dict(self):
        """Snapshotが正しく辞書に変換されること."""
        snapshot = Snapshot(
            run_id="test_run_1",
            query_package=QueryPackage(query="test query", source="pubmed"),
            search_results=[SearchResultItem(doc_id="pmid:12345", rank=1, score=0.95)],
        )

        data = snapshot.to_dict()

        assert data["run_id"] == "test_run_1"
        assert data["query_package"]["query"] == "test query"
        assert len(data["search_results"]["results"]) == 1

    def test_snapshot_from_dict(self):
        """Snapshotが辞書から正しく復元されること."""
        data = {
            "run_id": "test_run_2",
            "created_at": "2025-01-01T00:00:00",
            "query_package": {"query": "test", "source": "pubmed"},
            "search_results": {
                "total_count": 1,
                "results": [{"doc_id": "pmid:123", "rank": 1, "score": 0.9}],
            },
            "degraded": {"is_degraded": True, "reasons": ["API timeout"]},
        }

        snapshot = Snapshot.from_dict(data)

        assert snapshot.run_id == "test_run_2"
        assert snapshot.query_package.query == "test"
        assert len(snapshot.search_results) == 1
        assert snapshot.is_degraded is True
        assert "API timeout" in snapshot.degraded_reasons


class TestSnapshotManager:
    """スナップショットマネージャテスト."""

    def test_save_and_load(self):
        """保存と読込が正しく動作すること."""
        with TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(base_path=tmpdir, compress=False)

            snapshot = Snapshot(
                run_id="test_save_load", query_package=QueryPackage(query="save load test")
            )

            # 保存
            path = manager.save(snapshot)
            assert path.exists()

            # 読込
            loaded = manager.load("test_save_load")
            assert loaded is not None
            assert loaded.run_id == "test_save_load"
            assert loaded.query_package.query == "save load test"

    def test_save_compressed(self):
        """圧縮保存が動作すること."""
        with TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(base_path=tmpdir, compress=True)

            snapshot = Snapshot(run_id="compressed_test")
            path = manager.save(snapshot)

            assert path.suffix == ".gz"
            assert path.exists()

    def test_exists(self):
        """存在確認が正しく動作すること."""
        with TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(base_path=tmpdir, compress=False)

            assert manager.exists("nonexistent") is False

            snapshot = Snapshot(run_id="exists_test")
            manager.save(snapshot)

            assert manager.exists("exists_test") is True

    def test_content_hash(self):
        """コンテンツハッシュが決定的であること."""
        manager = SnapshotManager()

        hash1 = manager.get_content_hash("Hello World")
        hash2 = manager.get_content_hash("Hello World")
        hash3 = manager.get_content_hash("Hello World!")

        assert hash1 == hash2
        assert hash1 != hash3


class TestReproducibility:
    """再現性テスト."""

    def test_same_query_same_hash(self):
        """同一クエリは同一ハッシュを生成すること."""
        qp1 = QueryPackage(
            query="CD73 inhibitor tumor",
            source="pubmed",
            filters={"date_from": "2020-01-01"},
            max_results=20,
        )

        qp2 = QueryPackage(
            query="CD73 inhibitor tumor",
            source="pubmed",
            filters={"date_from": "2020-01-01"},
            max_results=20,
        )

        assert qp1.query_hash == qp2.query_hash

    def test_snapshot_roundtrip(self):
        """スナップショットのラウンドトリップが一致すること."""
        original = Snapshot(
            run_id="roundtrip_test",
            query_package=QueryPackage(query="roundtrip test"),
            search_results=[
                SearchResultItem(doc_id="pmid:1", rank=1, score=0.9),
                SearchResultItem(doc_id="pmid:2", rank=2, score=0.8),
            ],
            retrieved_content=[
                RetrievedContent(
                    doc_id="pmid:1",
                    content_hash="abc123",
                    title="Test Paper",
                    abstract="Test abstract",
                )
            ],
            chunk_mapping=[ChunkMapping(doc_id="pmid:1", chunk_id="c0", start=0, end=100)],
            model_io=[
                ModelIO(
                    stage_id="summarization.paper_digest",
                    model_id="gpt-4",
                    prompt_hash="prompt_hash_123",
                )
            ],
        )

        # 辞書経由でラウンドトリップ
        data = original.to_dict()
        restored = Snapshot.from_dict(data)

        assert restored.run_id == original.run_id
        assert len(restored.search_results) == len(original.search_results)
        assert len(restored.retrieved_content) == len(original.retrieved_content)
        assert len(restored.chunk_mapping) == len(original.chunk_mapping)
        assert len(restored.model_io) == len(original.model_io)


class TestDegradedRun:
    """degradedランテスト."""

    def test_degraded_flag_required(self):
        """degradedフラグが正しく設定されること."""
        snapshot = Snapshot(run_id="degraded_test")

        # 初期状態
        assert snapshot.is_degraded is False
        assert len(snapshot.degraded_reasons) == 0

        # degraded設定
        snapshot.is_degraded = True
        snapshot.degraded_reasons.append("API rate limit exceeded")

        data = snapshot.to_dict()
        assert data["degraded"]["is_degraded"] is True
        assert "API rate limit exceeded" in data["degraded"]["reasons"]

    def test_degraded_preserved_on_roundtrip(self):
        """degraded状態がラウンドトリップで保持されること."""
        original = Snapshot(
            run_id="degraded_roundtrip",
            is_degraded=True,
            degraded_reasons=["Partial retrieval", "Model timeout"],
        )

        data = original.to_dict()
        restored = Snapshot.from_dict(data)

        assert restored.is_degraded is True
        assert len(restored.degraded_reasons) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
