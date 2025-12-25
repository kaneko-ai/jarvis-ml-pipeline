"""
E2E Pipeline Tests - OA論文10本でフルパイプラインを検証

tests/e2e/oa_corpus.json を使用。
"""

import json
import pytest
from pathlib import Path

# Stage imports to trigger registration
import jarvis_core.stages  # noqa: F401

from jarvis_core.contracts.types import Artifacts, TaskContext
from jarvis_core.pipelines.executor import PipelineConfig, PipelineExecutor
from jarvis_core.pipelines.stage_registry import get_stage_registry


class TestE2EPipeline:
    """E2Eパイプラインテスト。"""
    
    @pytest.fixture
    def oa_corpus(self) -> dict:
        """OAコーパスを読み込み。"""
        corpus_path = Path(__file__).parent / "oa_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    @pytest.fixture
    def e2e_config(self) -> PipelineConfig:
        """E2Eパイプライン設定を読み込み。"""
        config_path = Path(__file__).parents[2] / "configs" / "pipelines" / "e2e_oa10.yml"
        return PipelineConfig.from_yaml(config_path)
    
    def test_oa_corpus_has_10_pmids(self, oa_corpus):
        """OAコーパスに10件のPMIDが含まれること。"""
        pmids = oa_corpus.get("pmids", [])
        assert len(pmids) == 10, f"Expected 10 PMIDs, got {len(pmids)}"
    
    def test_e2e_pipeline_stages_registered(self, e2e_config):
        """E2Eパイプラインの全ステージがregistryに登録されていること。"""
        registry = get_stage_registry()
        
        missing = []
        for stage in e2e_config.stages:
            if not registry.is_registered(stage):
                missing.append(stage)
        
        assert not missing, f"Missing stages: {missing}"
    
    def test_e2e_pipeline_config_valid(self, e2e_config):
        """パイプライン設定が有効であること。"""
        assert e2e_config.name == "e2e_oa10"
        assert len(e2e_config.stages) >= 10
        assert e2e_config.policies.get("provenance_required") is True
    
    def test_e2e_executor_can_be_created(self, e2e_config):
        """Executorがインスタンス化できること。"""
        executor = PipelineExecutor(e2e_config)
        assert executor is not None
        assert executor.config.name == "e2e_oa10"
    
    @pytest.mark.slow
    def test_e2e_pipeline_runs_with_mock_data(self, e2e_config, oa_corpus):
        """E2Eパイプラインがモックデータで完走すること。"""
        from jarvis_core.contracts.types import Paper
        
        executor = PipelineExecutor(e2e_config)
        
        # テスト用のコンテキストとartifacts
        context = TaskContext(
            goal=oa_corpus.get("query", "CD73 tumor microenvironment"),
            domain="oncology"
        )
        
        artifacts = Artifacts()
        
        # モック論文データを追加
        for i, pmid in enumerate(oa_corpus.get("pmids", [])[:3]):  # 最初の3本のみ
            artifacts.add_paper(Paper(
                doc_id=f"pmid:{pmid}",
                title=f"Test Paper {i+1}",
                abstract=f"This study demonstrates that CD73 plays a key role in tumor microenvironment. We show that inhibition of CD73 enhances antitumor immunity.",
                pmid=pmid
            ))
        
        # パイプライン実行
        result = executor.run(context, artifacts)
        
        # 結果検証
        assert result is not None
        assert result.metrics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
