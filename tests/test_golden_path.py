"""Golden Path回帰テスト.

Phase Loop 1: 壊れない一本道（Golden Path）の検証

テストケース:
1. 最小runが成功し、必須4ファイルが生成される
2. citation不足の場合、gate_passed=false, status=failed
3. show-runでfail理由が表示される
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from jarvis_core.storage import RunStore
from jarvis_core.eval.quality_gate import QualityGateVerifier, FailCodes


class TestArtifactContract:
    """成果物契約テスト（DEC-004）."""

    def test_required_artifacts_defined(self):
        """必須成果物が4ファイル定義されている."""
        assert len(RunStore.REQUIRED_ARTIFACTS) == 4
        assert "run_config.json" in RunStore.REQUIRED_ARTIFACTS
        assert "result.json" in RunStore.REQUIRED_ARTIFACTS
        assert "eval_summary.json" in RunStore.REQUIRED_ARTIFACTS
        assert "events.jsonl" in RunStore.REQUIRED_ARTIFACTS

    def test_validate_contract_all_present(self, tmp_path):
        """全成果物が存在する場合、契約違反なし."""
        run_id = "test-run-001"
        store = RunStore(run_id, base_dir=str(tmp_path))
        
        # 全ファイル作成
        (store.run_dir / "run_config.json").write_text("{}")
        (store.run_dir / "result.json").write_text("{}")
        (store.run_dir / "eval_summary.json").write_text("{}")
        (store.run_dir / "events.jsonl").write_text("")
        
        missing = store.validate_contract()
        assert missing == []

    def test_validate_contract_missing_files(self, tmp_path):
        """成果物が欠損している場合、契約違反を検出."""
        run_id = "test-run-002"
        store = RunStore(run_id, base_dir=str(tmp_path))
        
        # result.jsonのみ作成
        (store.run_dir / "result.json").write_text("{}")
        
        missing = store.validate_contract()
        assert len(missing) == 3
        assert "run_config.json" in missing
        assert "eval_summary.json" in missing
        assert "events.jsonl" in missing

    def test_get_summary_includes_contract_status(self, tmp_path):
        """get_summary()に契約検証結果が含まれる."""
        run_id = "test-run-003"
        store = RunStore(run_id, base_dir=str(tmp_path))
        
        summary = store.get_summary()
        assert "contract_valid" in summary
        assert "missing_artifacts" in summary
        assert summary["contract_valid"] is False  # ファイルなし


class TestSuccessCondition:
    """success条件テスト（DEC-005）."""

    def test_gate_passed_true_allows_success(self):
        """gate_passed=trueの場合、successが可能."""
        verifier = QualityGateVerifier()
        result = verifier.verify(
            answer="Test answer",
            citations=[{
                "paper_id": "p1",
                "claim_id": "c1",
                "evidence_text": "Evidence",
                "locator": {"section": "Methods", "paragraph": 1},
            }],
        )
        assert result.gate_passed is True

    def test_gate_passed_false_when_no_citations(self):
        """citation無しの場合、gate_passed=false."""
        verifier = QualityGateVerifier(require_citations=True)
        result = verifier.verify(
            answer="Test answer without citations",
            citations=[],
        )
        assert result.gate_passed is False
        
        # fail_reasonsに CITATION_MISSING が含まれる
        codes = [r.code for r in result.fail_reasons]
        assert FailCodes.CITATION_MISSING in codes

    def test_gate_passed_false_when_locator_missing(self):
        """locator無しの場合、gate_passed=false（設定時）."""
        verifier = QualityGateVerifier(require_locators=True)
        result = verifier.verify(
            answer="Test answer",
            citations=[{
                "paper_id": "p1",
                "claim_id": "c1",
                "evidence_text": "Evidence",
                # locator なし
            }],
        )
        assert result.gate_passed is False
        
        codes = [r.code for r in result.fail_reasons]
        assert FailCodes.LOCATOR_MISSING in codes

    def test_eval_summary_format(self):
        """eval_summary.json形式が正しい."""
        verifier = QualityGateVerifier()
        result = verifier.verify(
            answer="Test",
            citations=[],
        )
        
        eval_summary = result.to_eval_summary("test-run-id")
        
        assert "run_id" in eval_summary
        assert "status" in eval_summary
        assert "gate_passed" in eval_summary
        assert "fail_reasons" in eval_summary
        assert "metrics" in eval_summary
        assert eval_summary["run_id"] == "test-run-id"


class TestFailReasonCodes:
    """fail_reasonコードテスト."""

    def test_all_fail_codes_defined(self):
        """必要なfail_reasonコードが定義されている."""
        assert hasattr(FailCodes, "CITATION_MISSING")
        assert hasattr(FailCodes, "LOCATOR_MISSING")
        assert hasattr(FailCodes, "EVIDENCE_WEAK")
        assert hasattr(FailCodes, "ASSERTION_DANGER")
        assert hasattr(FailCodes, "PII_DETECTED")
        assert hasattr(FailCodes, "VERIFY_NOT_RUN")

    def test_assertion_danger_detection(self):
        """断定の危険を検出."""
        verifier = QualityGateVerifier()
        result = verifier.verify(
            answer="This is definitely true and will certainly happen.",
            citations=[{
                "paper_id": "p1",
                "claim_id": "c1",
                "evidence_text": "Evidence",
                "locator": {"section": "Results", "paragraph": 1},
            }],
        )
        
        # 断定の危険は警告レベル（gate_passedには影響しない可能性）
        codes = [r.code for r in result.fail_reasons]
        assert FailCodes.ASSERTION_DANGER in codes


class TestRunStoreSaveLoad:
    """RunStore保存・読み込みテスト."""

    def test_save_and_load_config(self, tmp_path):
        """run_config.jsonの保存と読み込み."""
        store = RunStore("test-run", base_dir=str(tmp_path))
        config = {"run_id": "test-run", "seed": 42, "model": "gpt-4"}
        
        store.save_config(config)
        loaded = store.load_config()
        
        assert loaded == config

    def test_save_and_load_result(self, tmp_path):
        """result.jsonの保存と読み込み."""
        store = RunStore("test-run", base_dir=str(tmp_path))
        result = {
            "run_id": "test-run",
            "status": "success",
            "answer": "Test answer",
        }
        
        store.save_result(result)
        loaded = store.load_result()
        
        assert loaded == result

    def test_save_and_load_eval(self, tmp_path):
        """eval_summary.jsonの保存と読み込み."""
        store = RunStore("test-run", base_dir=str(tmp_path))
        eval_data = {
            "run_id": "test-run",
            "gate_passed": True,
            "fail_reasons": [],
        }
        
        store.save_eval(eval_data)
        loaded = store.load_eval()
        
        assert loaded == eval_data


class TestGoldenPathIntegration:
    """Golden Path統合テスト（全体フロー）."""

    @pytest.mark.skip(reason="実行エンジンのモックが必要")
    def test_minimal_run_produces_all_artifacts(self, tmp_path):
        """最小runで全4ファイルが生成される."""
        # この テストは統合テストとして別途実装
        pass

    @pytest.mark.skip(reason="実行エンジンのモックが必要")
    def test_failed_run_still_produces_artifacts(self, tmp_path):
        """失敗runでも全4ファイルが生成される."""
        # この テストは統合テストとして別途実装
        pass
