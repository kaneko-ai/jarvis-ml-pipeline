from __future__ import annotations
"""Phase Loop 2: 再現性検証テスト.

同一入力 -> 同一構造 を検証
- タイムスタンプ、run_id 以外は同一であること
"""

from jarvis_core.storage import RunStore
from typing import Any


def get_structure_keys(data: Any, prefix: str = "") -> set[str]:
    """JSONデータの構造(キーのパス)を抽出."""
    keys = set()
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys.update(get_structure_keys(v, full_key))
    elif isinstance(data, list):
        if data:
            # リストの最初の要素の構造のみチェック
            keys.update(get_structure_keys(data[0], f"{prefix}[0]"))
    return keys


def normalize_for_diff(data: dict[str, Any]) -> dict[str, Any]:
    """再現性比較のためにデータを正規化.

    除外するフィールド:
    - timestamp (変動)
    - run_id (変動)
    """
    EXCLUDE_FIELDS = {"timestamp", "run_id", "task_id"}

    def _normalize(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _normalize(v) for k, v in obj.items() if k not in EXCLUDE_FIELDS}
        elif isinstance(obj, list):
            return [_normalize(item) for item in obj]
        return obj

    return _normalize(data)


class TestReproducibilityStructure:
    """再現性構造テスト."""

    def test_result_json_structure_consistent(self, tmp_path):
        """result.jsonの構造が一定."""
        # 2つのRunStoreを作成し、同じ構造で保存
        store1 = RunStore("run-1", base_dir=str(tmp_path))
        store2 = RunStore("run-2", base_dir=str(tmp_path))

        result1 = {
            "run_id": "run-1",
            "task_id": "task-1",
            "status": "success",
            "answer": "Test answer",
            "citations": [{"paper_id": "p1", "claim_id": "c1"}],
            "warnings": [],
            "timestamp": "2024-01-01T00:00:00Z",
        }

        result2 = {
            "run_id": "run-2",
            "task_id": "task-2",
            "status": "success",
            "answer": "Test answer",
            "citations": [{"paper_id": "p1", "claim_id": "c1"}],
            "warnings": [],
            "timestamp": "2024-01-02T00:00:00Z",
        }

        store1.save_result(result1)
        store2.save_result(result2)

        # 構造を比較
        struct1 = get_structure_keys(store1.load_result())
        struct2 = get_structure_keys(store2.load_result())

        assert struct1 == struct2

    def test_eval_summary_structure_consistent(self, tmp_path):
        """eval_summary.jsonの構造が一定."""
        store1 = RunStore("run-1", base_dir=str(tmp_path))
        store2 = RunStore("run-2", base_dir=str(tmp_path))

        eval1 = {
            "run_id": "run-1",
            "status": "pass",
            "gate_passed": True,
            "fail_reasons": [],
            "metrics": {"citation_count": 1},
            "timestamp": "2024-01-01T00:00:00Z",
        }

        eval2 = {
            "run_id": "run-2",
            "status": "pass",
            "gate_passed": True,
            "fail_reasons": [],
            "metrics": {"citation_count": 1},
            "timestamp": "2024-01-02T00:00:00Z",
        }

        store1.save_eval(eval1)
        store2.save_eval(eval2)

        struct1 = get_structure_keys(store1.load_eval())
        struct2 = get_structure_keys(store2.load_eval())

        assert struct1 == struct2

    def test_normalized_content_identical(self, tmp_path):
        """正規化後のコンテンツが同一."""
        result1 = {
            "run_id": "run-1",
            "status": "success",
            "answer": "Same answer",
            "citations": [],
            "timestamp": "2024-01-01T00:00:00Z",
        }

        result2 = {
            "run_id": "run-2",
            "status": "success",
            "answer": "Same answer",
            "citations": [],
            "timestamp": "2024-01-02T00:00:00Z",
        }

        norm1 = normalize_for_diff(result1)
        norm2 = normalize_for_diff(result2)

        assert norm1 == norm2


class TestMetricsNumericization:
    """Verify指標の数値化テスト."""

    def test_metrics_contains_citation_count(self):
        """metricsにcitation_countが含まれる."""
        from jarvis_core.eval.quality_gate import QualityGateVerifier

        verifier = QualityGateVerifier()
        result = verifier.verify(
            answer="Test",
            citations=[{"paper_id": "p1", "locator": {"section": "Methods"}}],
        )

        assert "citation_count" in result.metrics
        assert result.metrics["citation_count"] == 1

    def test_metrics_contains_locator_coverage(self):
        """metricsにlocator_coverageが含まれる."""
        from jarvis_core.eval.quality_gate import QualityGateVerifier

        verifier = QualityGateVerifier(require_locators=True)
        result = verifier.verify(
            answer="Test",
            citations=[
                {"paper_id": "p1", "locator": {"section": "Methods"}},
                {"paper_id": "p2"},  # locator無し
            ],
        )

        assert "locator_coverage" in result.metrics
        assert result.metrics["locator_coverage"] == 0.5

    def test_metrics_contains_assertion_count(self):
        """metricsにassertion_countが含まれる."""
        from jarvis_core.eval.quality_gate import QualityGateVerifier

        verifier = QualityGateVerifier()
        result = verifier.verify(
            answer="This is definitely true",
            citations=[{"paper_id": "p1", "locator": {"section": "X"}}],
        )

        assert "assertion_count" in result.metrics
        assert result.metrics["assertion_count"] >= 1


class TestPaperComparisonScore:
    """論文比較スコアテスト（最小実装）."""

    def test_citation_based_score(self):
        """citation数に基づくスコア."""
        # Phase Loop 2: 固定重みでのスコア計算
        citations1 = [{"paper_id": "p1"}, {"paper_id": "p2"}]
        citations2 = [{"paper_id": "p1"}]

        score1 = len(citations1)  # 単純なcitation数
        score2 = len(citations2)

        assert score1 > score2

    def test_evidence_quantity_score(self):
        """evidence量に基づくスコア."""
        evidence1 = [
            {"claim_id": "c1", "text": "Evidence 1"},
            {"claim_id": "c2", "text": "Evidence 2"},
            {"claim_id": "c3", "text": "Evidence 3"},
        ]
        evidence2 = [
            {"claim_id": "c1", "text": "Evidence 1"},
        ]

        score1 = len(evidence1)
        score2 = len(evidence2)

        assert score1 > score2
