"""
JARVIS Scientific Validity Tests

M5: 科学的妥当性のテスト
- 反証探索
- 論争マップ
- データセットガバナンス
"""

from jarvis_core.evaluation.counterevidence import (
    ControversyLevel,
    ControversyMapGenerator,
    CounterevidenceSearcher,
    EvidenceStance,
    check_one_sided_conclusion,
)
from jarvis_core.evaluation.dataset_governance import (
    DatasetGovernance,
    DatasetManifest,
)
from tempfile import TemporaryDirectory

import pytest


class TestCounterevidenceSearcher:
    """反証探索テスト."""

    def test_classify_supporting_stance(self):
        """支持スタンスを分類できること."""
        searcher = CounterevidenceSearcher()

        claim = "CD73 inhibition enhances antitumor immunity"
        evidence = "Our results support that CD73 blockade significantly improves tumor response"

        stance, confidence = searcher.classify_stance(claim, evidence)
        assert stance == EvidenceStance.SUPPORTING

    def test_classify_opposing_stance(self):
        """反対スタンスを分類できること."""
        searcher = CounterevidenceSearcher()

        claim = "CD73 inhibition enhances antitumor immunity"
        evidence = (
            "However, our study failed to show any effect. No significant difference was observed."
        )

        stance, confidence = searcher.classify_stance(claim, evidence)
        assert stance == EvidenceStance.OPPOSING

    def test_generate_counter_query(self):
        """反証用クエリを生成できること."""
        searcher = CounterevidenceSearcher()

        claim = "CD73 inhibition improves cancer treatment outcomes"
        query = searcher.generate_counter_query(claim)

        assert "NOT" in query or "fail" in query or "negative" in query

    def test_assess_controversy_none(self):
        """論争なしを評価できること."""
        searcher = CounterevidenceSearcher()

        level = searcher.assess_controversy(supporting_count=10, opposing_count=0)
        assert level == ControversyLevel.NONE

    def test_assess_controversy_high(self):
        """高論争を評価できること."""
        searcher = CounterevidenceSearcher()

        level = searcher.assess_controversy(supporting_count=5, opposing_count=4)
        assert level == ControversyLevel.HIGH

class TestControversyMapGenerator:
    """論争マップ生成テスト."""

    def test_generate_map(self):
        """論争マップを生成できること."""
        generator = ControversyMapGenerator()

        claims = [
            {"claim_id": "c1", "claim_text": "Treatment A is effective"},
            {"claim_id": "c2", "claim_text": "Treatment B has no effect"},
        ]

        evidence_by_claim = {
            "c1": [
                "Our study supports the effectiveness of treatment A",
                "However, we failed to replicate the effect in our cohort",
            ],
            "c2": ["Confirmed no significant effect of treatment B"],
        }

        controversy_map = generator.generate("test_run", claims, evidence_by_claim)

        assert controversy_map.run_id == "test_run"
        assert isinstance(controversy_map.summary, str)

    def test_map_to_dict(self):
        """論争マップを辞書に変換できること."""
        generator = ControversyMapGenerator()

        claims = [{"claim_id": "c1", "claim_text": "Test claim"}]
        evidence_by_claim = {"c1": ["Supporting evidence"]}

        controversy_map = generator.generate("test", claims, evidence_by_claim)
        data = controversy_map.to_dict()

        assert "run_id" in data
        assert "entries" in data
        assert "summary" in data

class TestOneSidedConclusion:
    """一方的結論チェックテスト."""

    def test_detects_violation(self):
        """一方的結論を検出できること."""
        from jarvis_core.evaluation.counterevidence import ControversyMap, ControversyMapEntry

        claims = [
            {"claim_id": "c1", "claim_text": "Controversial topic here", "is_main_conclusion": True}
        ]

        controversy_map = ControversyMap(run_id="test")
        controversy_map.entries.append(
            ControversyMapEntry(
                topic="Controversial topic here",
                claim_text="Controversial topic here",
                controversy_level=ControversyLevel.HIGH,
            )
        )

        has_violation, violations = check_one_sided_conclusion(claims, controversy_map)
        assert has_violation is True
        assert "c1" in violations

class TestDatasetGovernance:
    """データセットガバナンステスト."""

    def test_manifest_creation(self):
        """マニフェストを作成できること."""
        manifest = DatasetManifest(name="test_dataset", version="1.0.0", description="Test dataset")

        assert manifest.name == "test_dataset"
        assert manifest.total_records == 0

    def test_compute_record_hash(self):
        """レコードハッシュが一貫していること."""
        with TemporaryDirectory() as tmpdir:
            gov = DatasetGovernance(datasets_dir=tmpdir)

            record = {"input": "test", "output": "result"}
            hash1 = gov.compute_record_hash(record)
            hash2 = gov.compute_record_hash(record)

            assert hash1 == hash2

    def test_validate_record(self):
        """レコード検証が動作すること."""
        with TemporaryDirectory() as tmpdir:
            gov = DatasetGovernance(datasets_dir=tmpdir)

            # 有効なレコード
            valid_record = {"input": "test input", "output": "test output", "quality_score": 0.8}
            is_valid, reason = gov.validate_record(valid_record)
            assert is_valid is True

            # 品質が低いレコード
            low_quality = {"input": "test", "output": "test", "quality_score": 0.2}
            is_valid, reason = gov.validate_record(low_quality, min_quality=0.5)
            assert is_valid is False
            assert "Quality" in reason

    def test_append_to_dataset(self):
        """データセットに追加できること."""
        with TemporaryDirectory() as tmpdir:
            gov = DatasetGovernance(datasets_dir=tmpdir)

            records = [
                {"input": "q1", "output": "a1", "quality_score": 0.8},
                {"input": "q2", "output": "a2", "quality_score": 0.9},
            ]

            stats = gov.append_to_dataset("test_dataset", records)

            assert stats["added"] == 2
            assert stats["duplicate"] == 0

            # 重複追加
            stats2 = gov.append_to_dataset("test_dataset", records)
            assert stats2["duplicate"] == 2
            assert stats2["added"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
