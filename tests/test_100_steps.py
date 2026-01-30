"""
JARVIS 100-Step Verification Tests

Step 99-100: 最小の強い核が壊れずに拡張できることを確認
"""

import json


class TestRunStore:
    """RunStore契約テスト."""

    def test_generate_run_id(self):
        """run_id生成規約."""
        from jarvis_core.storage.run_store_v2 import generate_run_id

        run_id = generate_run_id()

        # フォーマット: YYYYMMDD_HHMMSS_<uuid>
        parts = run_id.split("_")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS
        assert len(parts[2]) == 8  # UUID

    def test_run_context_saves_required_files(self, tmp_path):
        """必須ファイルが保存される."""
        from jarvis_core.storage.run_store_v2 import RunStore

        store = RunStore(str(tmp_path))
        ctx = store.create_run()

        # 必須ファイルを保存
        ctx.save_input({"goal": "test"})
        ctx.save_config({"pipeline": "test"})
        ctx.save_result({"status": "success", "answer": "test", "citations": []})
        ctx.save_eval_summary({"gate_passed": True, "fail_reasons": [], "metrics": {}})
        ctx.save_papers([])
        ctx.save_claims([])
        ctx.save_evidence([])
        ctx.save_scores({"features": {}})
        ctx.save_report("# Report")
        ctx.save_warnings([])

        # 全ファイル存在
        assert ctx.is_complete()


class TestQualityGate:
    """品質ゲートテスト."""

    def test_citation_required(self):
        """引用必須."""
        from jarvis_core.eval.quality_gate import FailCodes, QualityGateVerifier

        verifier = QualityGateVerifier(require_citations=True)
        result = verifier.verify(answer="Test answer", citations=[])

        assert not result.gate_passed
        assert any(r.code == FailCodes.CITATION_MISSING for r in result.fail_reasons)

    def test_citation_passes(self):
        """引用があれば成功."""
        from jarvis_core.eval.quality_gate import QualityGateVerifier

        verifier = QualityGateVerifier(require_citations=True, require_locators=False)
        result = verifier.verify(
            answer="Test answer",
            citations=[{"paper_id": "1", "evidence_text": "test"}],
        )

        assert result.gate_passed

    def test_assertion_detection(self):
        """断定検出."""
        from jarvis_core.eval.quality_gate import FailCodes, QualityGateVerifier

        verifier = QualityGateVerifier(require_citations=False)
        result = verifier.verify(
            answer="This is definitely true and absolutely certain.",
            citations=[],
        )

        # 断定はwarningなのでgate_passedはTrue
        assert any(r.code == FailCodes.ASSERTION_DANGER for r in result.fail_reasons)


class TestJudge:
    """Judgeテスト."""

    def test_two_system_judge(self):
        """2系統Judge."""
        from jarvis_core.eval.judge import Judge

        judge = Judge()
        result = judge.judge(
            result={"answer": "test", "citations": []},
            claims=[{"claim_id": "1", "text": "claim"}],
            evidence=[{"claim_id": "1", "text": "evidence"}],
        )

        assert result.format_score >= 0
        assert result.citation_score >= 0
        assert result.overall_score >= 0


class TestRetryManager:
    """再試行テスト."""

    def test_max_retries(self):
        """最大再試行."""
        from jarvis_core.eval.judge import RetryManager

        manager = RetryManager(max_retries=3)

        assert manager.should_retry(["CITATION_MISSING"], 0)
        assert manager.should_retry(["CITATION_MISSING"], 1)
        assert manager.should_retry(["CITATION_MISSING"], 2)
        assert not manager.should_retry(["CITATION_MISSING"], 3)

    def test_cost_limit(self):
        """コスト上限."""
        from jarvis_core.eval.judge import RetryManager

        manager = RetryManager(max_retries=10, cost_limit=5.0)

        # コストを積み上げ
        manager.record_attempt(1, [], False, 2.0, 100)
        manager.record_attempt(2, [], False, 2.0, 100)
        manager.record_attempt(3, [], False, 2.0, 100)  # 6.0 > 5.0

        assert not manager.should_retry(["CITATION_MISSING"], 3)


class TestRunAPI:
    """RunAPIテスト."""

    def test_get_status_returns_result(self, tmp_path):
        """ステータス取得."""
        from jarvis_core.api.run_api import RunAPI

        # テストデータ作成
        run_id = "test_run"
        run_dir = tmp_path / run_id
        run_dir.mkdir()

        result = {"run_id": run_id, "status": "success"}
        (run_dir / "result.json").write_text(json.dumps(result))

        api = RunAPI(str(tmp_path))
        status = api.get_status(run_id)

        assert status["status"] == "success"


class TestSecurityOps:
    """セキュリティテスト."""

    def test_pii_detection(self):
        """PII検出."""
        from jarvis_core.ops.security_ops import PIIDetector

        text = "Contact: test@example.com, 123-45-6789"
        findings = PIIDetector.detect(text)

        assert len(findings) >= 2
        types = [f["type"] for f in findings]
        assert "email" in types
        assert "ssn" in types

    def test_pii_masking(self):
        """PIIマスク."""
        from jarvis_core.ops.security_ops import PIIDetector

        text = "SSN: 123-45-6789"
        masked = PIIDetector.mask(text)

        assert "123-45-6789" not in masked
        assert "[REDACTED]" in masked


class TestBundleContract:
    """Bundle契約テスト（Step 99-100）."""

    def test_bundle_validation(self, tmp_path):
        """Bundle検証."""
        from jarvis_core.storage.run_store_v2 import REQUIRED_FILES, RunStore

        store = RunStore(str(tmp_path))
        ctx = store.create_run()

        # 空状態
        status = ctx.get_bundle_status()
        assert not all(status.values())

        # 必須ファイル作成
        for filename in REQUIRED_FILES:
            path = ctx.run_dir / filename
            if filename.endswith(".json"):
                path.write_text("{}")
            elif filename.endswith(".jsonl"):
                path.write_text("")
            elif filename.endswith(".md"):
                path.write_text("# Test")

        # 完全状態
        assert ctx.is_complete()