"""
JARVIS Pretrain Meta-Analysis Core Tests

系統B: メタ分析コアパイプラインのテスト
- PICO抽出
- 効果量抽出
- バイアスリスク評価
- 抽出精度プロキシ
"""

import jarvis_core.stages  # noqa: F401
from jarvis_core.contracts.types import Artifacts, TaskContext
from jarvis_core.pipelines.executor import PipelineConfig
from jarvis_core.pipelines.stage_registry import get_stage_registry
from pathlib import Path

import pytest

# Stage imports


class TestPrimaryStudyFilter:
    """一次研究フィルターテスト。"""

    def test_excludes_reviews(self):
        """レビュー論文を除外すること。"""
        from jarvis_core.stages.pretrain_meta import stage_primary_study_filter

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["primary_search_results"] = [
            {"pmid": "1", "title": "Randomized Trial of X"},
            {"pmid": "2", "title": "Systematic Review of Y"},
            {"pmid": "3", "title": "Meta-analysis of Z interventions"},
            {"pmid": "4", "title": "Cohort Study of W"},
        ]

        result = stage_primary_study_filter(context, artifacts)

        included = result.metadata.get("primary_studies", [])
        excluded = result.metadata.get("excluded_reviews", [])

        # RCT, Cohortは含まれる
        included_pmids = [p["pmid"] for p in included]
        assert "1" in included_pmids
        assert "4" in included_pmids

        # Review, Meta-analysisは除外
        excluded_pmids = [p["pmid"] for p in excluded]
        assert "2" in excluded_pmids
        assert "3" in excluded_pmids


class TestPICOExtraction:
    """PICO抽出テスト。"""

    def test_extracts_pico_for_each_study(self):
        """各研究に対してPICOを抽出すること。"""
        from jarvis_core.stages.pretrain_meta import stage_extraction_pico

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["primary_studies"] = [
            {"pmid": "1", "title": "Study 1"},
            {"pmid": "2", "title": "Study 2"},
        ]

        result = stage_extraction_pico(context, artifacts)

        pico = result.metadata.get("pico_extractions", [])
        assert len(pico) == 2

        for p in pico:
            assert "pmid" in p
            assert "population" in p
            assert "intervention" in p
            assert "comparison" in p
            assert "outcome" in p


class TestBiasRiskAssessment:
    """バイアスリスク評価テスト。"""

    def test_evaluates_rob_domains(self):
        """RoBドメインを評価すること。"""
        from jarvis_core.stages.pretrain_meta import stage_extraction_bias_risk

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["primary_studies"] = [{"pmid": "1", "title": "Study 1"}]

        result = stage_extraction_bias_risk(context, artifacts)

        assessments = result.metadata.get("bias_assessments", [])
        assert len(assessments) == 1

        assessment = assessments[0]
        assert "domains" in assessment
        assert "overall_bias" in assessment

        # 必須ドメイン
        required_domains = [
            "randomization",
            "deviations",
            "missing_data",
            "outcome_measurement",
            "selective_reporting",
        ]

        for domain in required_domains:
            assert domain in assessment["domains"]


class TestExtractionAccuracyProxy:
    """抽出精度プロキシテスト。"""

    def test_calculates_metrics(self):
        """メトリクスを正しく計算すること。"""
        from jarvis_core.stages.pretrain_meta import stage_extraction_accuracy_proxy

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["pico_extractions"] = [
            {"population": "Adults", "intervention": "Drug A", "outcome": "Survival"}
        ]
        artifacts.metadata["outcome_extractions"] = [{"pmid": "1"}]
        artifacts.metadata["effect_size_data"] = [{"extracted": False}]
        artifacts.metadata["bias_assessments"] = [{"pmid": "1"}]

        result = stage_extraction_accuracy_proxy(context, artifacts)

        accuracy = result.metadata.get("extraction_accuracy_proxy", {})
        assert "pico_completeness" in accuracy
        assert "effect_extraction_rate" in accuracy
        assert "overall_score" in accuracy
        assert 0 <= accuracy["overall_score"] <= 1


class TestStoreTrainingRecordMeta:
    """メタ分析学習レコード保存テスト。"""

    def test_creates_record_with_all_fields(self):
        """全フィールドを含むレコードを作成すること。"""
        from unittest.mock import MagicMock, patch

        from jarvis_core.stages.pretrain_meta import stage_store_training_record_meta

        context = TaskContext(goal="test query", domain="test", run_id="test_run")
        artifacts = Artifacts()

        artifacts.metadata["meta_seed_query"] = "test query"
        artifacts.metadata["primary_studies"] = [{"pmid": "1"}]
        artifacts.metadata["pico_extractions"] = []
        artifacts.metadata["outcome_extractions"] = []
        artifacts.metadata["effect_size_data"] = []
        artifacts.metadata["bias_assessments"] = []
        artifacts.metadata["extraction_accuracy_proxy"] = {"overall_score": 0.8}

        with patch("builtins.open", MagicMock()):
            with patch.object(Path, "mkdir"):
                result = stage_store_training_record_meta(context, artifacts)

        assert "meta_training_record_saved" in result.metadata


class TestPipelineStagesRegistered:
    """パイプラインステージ登録テスト。"""

    def test_all_meta_core_stages_registered(self):
        """メタ分析コアパイプラインの全ステージが登録されていること。"""
        registry = get_stage_registry()

        required_stages = [
            "retrieval.seed_topic_or_query",
            "retrieval.search_pubmed_primary",
            "screening.primary_study_filter",
            "extraction.pico",
            "extraction.outcomes",
            "extraction.effect_size_fields",
            "extraction.bias_risk_rob",
            "evaluation.extraction_accuracy_proxy",
            "ops.store_training_record_meta",
        ]

        for stage in required_stages:
            assert registry.is_registered(stage), f"Stage {stage} not registered"

    def test_pipeline_yaml_is_valid(self):
        """パイプラインYAMLが有効であること。"""
        config_path = Path(__file__).parents[1] / "configs" / "pipelines" / "pretrain_meta_core.yml"

        if config_path.exists():
            config = PipelineConfig.from_yaml(config_path)
            assert config.name == "pretrain_meta_core"
            assert len(config.stages) >= 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])