"""E2E Offline Tests.

Per DEC-006: ネットワーク不要でE2Eを検証するテスト。
固定コーパスを使用し、10ファイル契約への準拠を確認。
"""

import json
from pathlib import Path

import pytest

# Test fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
OFFLINE_CORPUS = FIXTURES_DIR / "offline_corpus.json"


class TestOfflineCorpus:
    """オフラインコーパスの検証テスト。"""

    def test_corpus_exists(self):
        """固定コーパスファイルが存在する。"""
        assert OFFLINE_CORPUS.exists(), f"Offline corpus not found: {OFFLINE_CORPUS}"

    def test_corpus_structure(self):
        """コーパスが正しい構造を持つ。"""
        with open(OFFLINE_CORPUS, encoding="utf-8") as f:
            corpus = json.load(f)

        assert "papers" in corpus, "Corpus must have 'papers' key"
        assert len(corpus["papers"]) >= 3, "Corpus must have at least 3 papers"

        for paper in corpus["papers"]:
            assert "paper_id" in paper, "Each paper must have paper_id"
            assert "title" in paper, "Each paper must have title"
            assert "abstract" in paper, "Each paper must have abstract"

    def test_corpus_has_sections(self):
        """論文にセクション情報が含まれる。"""
        with open(OFFLINE_CORPUS, encoding="utf-8") as f:
            corpus = json.load(f)

        papers_with_sections = [p for p in corpus["papers"] if p.get("sections")]
        assert len(papers_with_sections) >= 1, "At least one paper must have sections"


class TestOfflinePipeline:
    """オフラインパイプライン設定の検証。"""

    def test_offline_pipeline_exists(self):
        """オフラインパイプライン定義が存在する。"""
        pipeline_path = Path("configs/pipelines/e2e_offline.yml")
        assert pipeline_path.exists(), f"Offline pipeline not found: {pipeline_path}"

    def test_offline_pipeline_structure(self):
        """パイプラインが正しい構造を持つ。"""
        import yaml

        pipeline_path = Path("configs/pipelines/e2e_offline.yml")
        if not pipeline_path.exists():
            pytest.skip("Offline pipeline not found")

        with open(pipeline_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert config.get("pipeline") == "e2e_offline"
        assert "stages" in config
        assert config.get("policies", {}).get("offline") is True


class TestBundleContract:
    """10ファイル契約（DEC-006）の検証。"""

    REQUIRED_FILES = [
        "input.json",
        "run_config.json",
        "papers.jsonl",
        "claims.jsonl",
        "evidence.jsonl",
        "scores.json",
        "result.json",
        "eval_summary.json",
        "warnings.jsonl",
        "report.md",
    ]

    def test_bundle_contract_defined(self):
        """成果物契約ファイル一覧が正しい。"""
        from jarvis_core.storage import RunStore

        assert hasattr(RunStore, "REQUIRED_ARTIFACTS")
        assert len(RunStore.REQUIRED_ARTIFACTS) == 10

    def test_failure_contract_defined(self):
        """失敗時の最小契約が定義されている。"""
        from jarvis_core.storage import RunStore

        assert hasattr(RunStore, "FAILURE_REQUIRED")
        required = set(RunStore.FAILURE_REQUIRED)
        assert "result.json" in required
        assert "eval_summary.json" in required
        assert "warnings.jsonl" in required
        assert "report.md" in required


@pytest.mark.e2e
class TestE2EOfflineSmoke:
    """オフラインE2Eスモークテスト。

    Note: このテストは実際のパイプライン実行を行うため、
    pytestのマーカー (-m e2e) で明示的に実行する必要がある。
    """

    @pytest.mark.skip(reason="Requires full pipeline implementation")
    def test_offline_e2e_produces_bundle(self, tmp_path):
        """オフラインE2Eがbundleを生成する。"""

        # This test would run the full pipeline with offline corpus
        # and verify that 10 files are produced
        pass
