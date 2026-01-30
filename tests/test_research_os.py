"""
JARVIS Research OS Tests

Provider、Trend Watcher、BibTeX、Memory、Multi-Judgeのテスト
"""

from jarvis_core.evaluation.multi_judge import (
    MultiJudgeEvaluator,
)
from jarvis_core.memory.hindsight import (
    HindsightMemory,
    MemoryType,
)
from jarvis_core.providers.api_llm import APILLMProvider
from jarvis_core.providers.base import ProviderConfig, ProviderType
from jarvis_core.providers.local_llm import LocalLLMProvider
from jarvis_core.trend.ranker import TrendRanker
from jarvis_core.trend.sources import TrendItem
from tempfile import TemporaryDirectory
import pytest


# Evaluator tests

# Memory tests

# Provider tests

# Trend tests


class TestProviders:
    """Provider tests."""

    def test_provider_config(self):
        """ProviderConfigが作成できること."""
        config = ProviderConfig(
            provider_type=ProviderType.API,
            model="gpt-4o-mini",
        )
        assert config.provider_type == ProviderType.API
        assert config.model == "gpt-4o-mini"

    def test_api_llm_provider(self):
        """APILLMProviderが初期化できること."""
        config = ProviderConfig(provider_type=ProviderType.API, model="test")
        provider = APILLMProvider(config)
        assert provider.provider_type == ProviderType.API

    def test_local_llm_provider(self):
        """LocalLLMProviderが初期化できること."""
        config = ProviderConfig(
            provider_type=ProviderType.LOCAL,
            model="qwen2.5",
            backend="ollama",
        )
        provider = LocalLLMProvider(config)
        assert provider.provider_type == ProviderType.LOCAL


class TestTrendRanker:
    """TrendRanker tests."""

    def test_rank_items(self):
        """アイテムをランキングできること."""
        ranker = TrendRanker()

        items = [
            TrendItem(
                id="1",
                title="Machine Learning for Research",
                source="arxiv",
                url="https://arxiv.org/abs/1",
                abstract="This paper discusses machine learning...",
            ),
            TrendItem(
                id="2",
                title="Random topic",
                source="blog",
                url="https://example.com/2",
            ),
        ]

        ranked = ranker.rank(items)

        # arXiv + ML関連は上位に
        assert ranked[0][0].id == "1"
        assert ranked[0][1].total > ranked[1][1].total


class TestHindsightMemory:
    """HindsightMemory tests."""

    def test_add_world_requires_evidence(self):
        """World追加には根拠が必須であること."""
        with TemporaryDirectory() as tmpdir:
            memory = HindsightMemory(storage_path=tmpdir)

            with pytest.raises(ValueError):
                memory.add_world(
                    content="Test fact",
                    source="test",
                    evidence=[],  # 空の根拠
                )

    def test_add_world_with_evidence(self):
        """根拠付きでWorld追加できること."""
        with TemporaryDirectory() as tmpdir:
            memory = HindsightMemory(storage_path=tmpdir)

            entry = memory.add_world(
                content="Verified fact",
                source="paper",
                evidence=["DOI:10.1234/test"],
            )

            assert entry.memory_type == MemoryType.WORLD
            assert entry.verified is True

    def test_add_experience(self):
        """Experience追加ができること."""
        with TemporaryDirectory() as tmpdir:
            memory = HindsightMemory(storage_path=tmpdir)

            entry = memory.add_experience(
                content="Ran experiment X",
                source="manual",
            )

            assert entry.memory_type == MemoryType.EXPERIENCE

    def test_add_opinion_isolated(self):
        """Opinionは隔離されること."""
        with TemporaryDirectory() as tmpdir:
            memory = HindsightMemory(storage_path=tmpdir)

            entry = memory.add_opinion(
                content="I think X is better",
                source="personal",
            )

            assert entry.memory_type == MemoryType.OPINION
            assert entry.verified is False

    def test_promote_observation_to_world(self):
        """Observationは根拠付きでWorldに昇格できること."""
        with TemporaryDirectory() as tmpdir:
            memory = HindsightMemory(storage_path=tmpdir)

            obs = memory.add_observation(
                content="Observed behavior",
                source="test",
            )

            world = memory.promote_to_world(
                observation_id=obs.id,
                evidence=["Verified by experiment"],
                verification_method="experiment",
            )

            assert world.memory_type == MemoryType.WORLD
            assert world.verified is True


class TestMultiJudgeEvaluator:
    """MultiJudgeEvaluator tests."""

    def test_evaluate_with_evidence(self):
        """根拠付きで評価できること."""
        evaluator = MultiJudgeEvaluator()

        result = evaluator.evaluate(
            item_id="test1",
            content="This claim is supported by evidence",
            evidence=["DOI:10.1234/paper"],
        )

        assert len(result.verdicts) == 3  # 3 judges
        assert result.final_score > 0

    def test_evaluate_without_evidence_disqualified(self):
        """根拠なしは失格になること."""
        evaluator = MultiJudgeEvaluator()

        result = evaluator.evaluate(
            item_id="test2",
            content="This claim has no evidence",
            evidence=[],
        )

        assert result.disqualified is True
        assert result.final_approved is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])