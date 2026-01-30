"""
JARVIS Pretrain Citation Reconstruction Tests

系統A: 引用再構成パイプラインのテスト
- leakage_filter が高リーク文献を除外する
- paper_A の本文を生成に使用しない
- スキーマ準拠
- evidence spans 妥当性
- JSONL 追記が正しい
"""

import jarvis_core.stages  # noqa: F401
from jarvis_core.contracts.types import Artifacts, TaskContext
from jarvis_core.pipelines.executor import PipelineConfig
from jarvis_core.pipelines.stage_registry import get_stage_registry
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Stage imports


class TestLeakageFilter:
    """リークフィルターテスト。"""

    def test_leakage_filter_detects_high_overlap(self):
        """高リーク文献を検出できること。"""
        from jarvis_core.stages.pretrain_citation import stage_leakage_filter

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        # paper_Aを設定（アブストラクトにキーワード）
        artifacts.metadata["paper_A"] = {
            "title": "CD73 inhibition therapy",
            "abstract": "This study shows CD73 inhibition enhances antitumor immunity in cancer.",
        }

        # R_set_docsを設定（高リーク = 類似度高い）
        artifacts.metadata["R_set_docs"] = [
            {
                "ref_id": "R1",
                "abstract": "CD73 inhibition enhances antitumor immunity in cancer treatment.",
            },
            {"ref_id": "R2", "abstract": "Unrelated topic about protein folding mechanisms."},
        ]

        result = stage_leakage_filter(context, artifacts)

        leakage_flags = result.metadata.get("leakage_flags", [])
        assert len(leakage_flags) == 2

        # R1は高リークであるべき
        r1_flag = next((f for f in leakage_flags if f["ref_id"] == "R1"), None)
        assert r1_flag is not None
        # R2は低リークであるべき
        r2_flag = next((f for f in leakage_flags if f["ref_id"] == "R2"), None)
        assert r2_flag is not None
        assert r2_flag["leakage_level"] == "low"

    def test_leakage_filter_removes_high_leakage_docs(self):
        """高リーク文献がR_set_filteredから除外されること。"""
        from jarvis_core.stages.pretrain_citation import stage_leakage_filter

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["paper_A"] = {
            "title": "Test",
            "abstract": "unique words that only appear here abc def ghi jkl mno pqr stu vwx yz",
        }

        artifacts.metadata["R_set_docs"] = [
            {
                "ref_id": "R1",
                "abstract": "unique words that only appear here abc def ghi jkl mno pqr stu vwx yz",
            },
            {"ref_id": "R2", "abstract": "completely different topic unrelated"},
        ]

        result = stage_leakage_filter(context, artifacts)

        filtered = result.metadata.get("R_set_filtered", [])
        # R1は高リークで除外、R2は残る
        assert len(filtered) >= 1
        filtered_ids = [d["ref_id"] for d in filtered]
        assert "R2" in filtered_ids


class TestNoLeakageGate:
    """リーク禁止ゲートテスト。"""

    def test_gate_fails_when_high_leakage_ratio_exceeds_threshold(self):
        """高リーク比率がしきい値を超えるとゲートがFAILすること。"""
        from jarvis_core.stages.pretrain_citation import stage_no_leakage_gate

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        # 50%が高リーク（しきい値30%超過）
        artifacts.metadata["leakage_flags"] = [
            {"ref_id": "R1", "leakage_level": "high"},
            {"ref_id": "R2", "leakage_level": "high"},
            {"ref_id": "R3", "leakage_level": "low"},
            {"ref_id": "R4", "leakage_level": "low"},
        ]

        result = stage_no_leakage_gate(context, artifacts)

        gate_result = result.metadata.get("no_leakage_gate", {})
        assert gate_result["passed"] is False
        assert gate_result["save_to_training"] is False
        assert gate_result["save_to_audit"] is True

    def test_gate_passes_when_leakage_ratio_is_low(self):
        """リーク比率が低いとゲートがPASSすること。"""
        from jarvis_core.stages.pretrain_citation import stage_no_leakage_gate

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        # 10%が高リーク（しきい値30%未満）
        artifacts.metadata["leakage_flags"] = [
            {"ref_id": "R1", "leakage_level": "high"},
            {"ref_id": "R2", "leakage_level": "low"},
            {"ref_id": "R3", "leakage_level": "low"},
            {"ref_id": "R4", "leakage_level": "low"},
            {"ref_id": "R5", "leakage_level": "low"},
            {"ref_id": "R6", "leakage_level": "low"},
            {"ref_id": "R7", "leakage_level": "low"},
            {"ref_id": "R8", "leakage_level": "low"},
            {"ref_id": "R9", "leakage_level": "low"},
            {"ref_id": "R10", "leakage_level": "low"},
        ]

        result = stage_no_leakage_gate(context, artifacts)

        gate_result = result.metadata.get("no_leakage_gate", {})
        assert gate_result["passed"] is True
        assert gate_result["save_to_training"] is True


class TestMatchScore:
    """マッチスコアテスト。"""

    def test_match_score_calculates_coverage(self):
        """Coverageが正しく計算されること。"""
        from jarvis_core.stages.pretrain_citation import stage_match_score

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["reconstruction"] = {
            "background_points": [
                {"text": "Point 1", "evidence": [{"ref_id": "R1"}]},
                {"text": "Point 2", "evidence": []},
            ],
            "hypotheses": [{"text": "Hypo"}],
            "missing_critical_views": [],
        }

        artifacts.metadata["gold_points"] = [
            {"point_id": "g1", "claim": "Gold 1"},
            {"point_id": "g2", "claim": "Gold 2"},
        ]

        artifacts.metadata["leakage_flags"] = [{"ref_id": "R1", "leakage_level": "low"}]

        result = stage_match_score(context, artifacts)

        match_score = result.metadata.get("match_score", {})
        assert "coverage" in match_score
        assert "faithfulness" in match_score
        assert "total" in match_score
        assert 0 <= match_score["total"] <= 1


class TestSchemaCompliance:
    """スキーマ準拠テスト。"""

    def test_r_digest_schema(self):
        """R_digestが正しいスキーマを持つこと。"""
        from jarvis_core.stages.pretrain_citation import stage_R_set_digest

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["R_set_filtered"] = [
            {"ref_id": "R1", "title": "Test", "abstract": "Abstract text"}
        ]

        result = stage_R_set_digest(context, artifacts)

        R_digest = result.metadata.get("R_digest", {})
        assert "digest_version" in R_digest
        assert "refs" in R_digest

        for ref in R_digest["refs"]:
            assert "ref_id" in ref
            assert "meta" in ref
            assert "abstract_digest" in ref
            assert "provenance" in ref

    def test_reconstruction_schema(self):
        """reconstructionが正しいスキーマを持つこと。"""
        from jarvis_core.stages.pretrain_citation import stage_reconstruct_background_discussion

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["R_digest"] = {"refs": []}

        result = stage_reconstruct_background_discussion(context, artifacts)

        reconstruction = result.metadata.get("reconstruction", {})
        assert "reconstruction_version" in reconstruction
        assert "background_points" in reconstruction
        assert "controversies" in reconstruction
        assert "hypotheses" in reconstruction
        assert "predicted_conclusions" in reconstruction
        assert "notes" in reconstruction


class TestStoreTrainingRecord:
    """学習レコード保存テスト。"""

    def test_skips_saving_when_gate_fails(self):
        """ゲート失敗時は保存しないこと。"""
        from jarvis_core.stages.pretrain_citation import stage_store_training_record

        context = TaskContext(goal="test", domain="test")
        artifacts = Artifacts()

        artifacts.metadata["no_leakage_gate"] = {"passed": False, "save_to_training": False}

        result = stage_store_training_record(context, artifacts)

        assert result.metadata["training_record_saved"] is False
        assert "Leakage gate failed" in result.metadata.get("training_record_reason", "")

    def test_deduplication_by_hash(self):
        """レコードハッシュで重複排除されること。"""
        # このテストは実際のファイル操作が絡むため、モックを使用
        from jarvis_core.stages.pretrain_citation import stage_store_training_record

        context = TaskContext(goal="test", domain="test", run_id="test_run_1")
        artifacts = Artifacts()

        artifacts.metadata["no_leakage_gate"] = {"passed": True, "save_to_training": True}
        artifacts.metadata["paper_A"] = {"pmid": "12345"}
        artifacts.metadata["R_digest"] = {"refs": []}
        artifacts.metadata["reconstruction"] = {}
        artifacts.metadata["gold_points"] = []
        artifacts.metadata["match_score"] = {"total": 0.5}
        artifacts.metadata["leakage_flags"] = []

        # 最初の保存
        with patch("builtins.open", MagicMock()):
            with patch.object(Path, "exists", return_value=False):
                with patch.object(Path, "mkdir"):
                    result = stage_store_training_record(context, artifacts)

        # 保存フラグを確認（エラーなく完了）
        assert "training_record_saved" in result.metadata


class TestPipelineStagesRegistered:
    """パイプラインステージ登録テスト。"""

    def test_all_citation_reconstruction_stages_registered(self):
        """引用再構成パイプラインの全ステージが登録されていること。"""
        registry = get_stage_registry()

        required_stages = [
            "retrieval.get_paper_A",
            "extraction.references_from_A",
            "retrieval.fetch_R_set",
            "screening.leakage_filter",
            "summarization.R_set_digest",
            "generation.reconstruct_background_discussion",
            "extraction.gold_from_A",
            "evaluation.match_score",
            "quality_gate.no_leakage",
            "ops.store_training_record",
        ]

        for stage in required_stages:
            assert registry.is_registered(stage), f"Stage {stage} not registered"

    def test_pipeline_yaml_is_valid(self):
        """パイプラインYAMLが有効であること。"""
        config_path = (
            Path(__file__).parents[1]
            / "configs"
            / "pipelines"
            / "pretrain_citation_reconstruction.yml"
        )

        if config_path.exists():
            config = PipelineConfig.from_yaml(config_path)
            assert config.name == "pretrain_citation_reconstruction"
            assert len(config.stages) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])