"""
JARVIS Phase2 Tests

類似判断検索の強制化テスト
"""

from jarvis_core.intelligence.goldset_index import (
    GoldsetEntry,
    GoldsetIndex,
)
from jarvis_core.intelligence.mandatory_search import (
    MandatorySearchJudge,
    Phase2Decision,
)
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


class TestGoldsetIndex:
    """GoldsetIndex テスト."""

    def test_entry_embedding_text(self):
        """embedding_textが生成できること."""
        entry = GoldsetEntry(
            context="論文RAGの設計",
            decision="accept",
            scores={"relevance": 5},
            reason="初期は速度優先",
            outcome="大量論文を扱えた",
        )

        text = entry.generate_embedding_text()

        assert "Context: 論文RAGの設計" in text
        assert "Decision: accept" in text
        assert "Reason: 初期は速度優先" in text
        assert "Outcome: 大量論文を扱えた" in text

    def test_keyword_search(self):
        """キーワード検索ができること."""
        with TemporaryDirectory() as tmpdir:
            # 一時的なgoldsetを作成
            goldset_path = Path(tmpdir) / "test_goldset.jsonl"
            goldset_path.write_text(
                '{"context":"論文RAG設計","decision":"accept","scores":{},"reason":"速度優先","outcome":"成功"}\n'
                '{"context":"Graph RAG導入","decision":"reject","scores":{},"reason":"時期尚早","outcome":"正解"}\n',
                encoding="utf-8",
            )

            index = GoldsetIndex(goldset_path=str(goldset_path), index_path=tmpdir)

            # 検索（embedding未使用）
            results = index._keyword_search("論文RAG設計", top_k=2)

            assert len(results) > 0
            assert results[0][0].context == "論文RAG設計"


class TestMandatorySearchJudge:
    """MandatorySearchJudge テスト."""

    def test_judge_with_similar_search(self):
        """類似検索付き判断ができること."""
        with TemporaryDirectory() as tmpdir:
            # 一時的なgoldsetを作成
            goldset_path = Path(tmpdir) / "goldset.jsonl"
            goldset_path.write_text(
                '{"context":"API/Local切替設計","decision":"accept","scores":{"relevance":5},"reason":"機密性重要","outcome":"自由度向上"}\n',
                encoding="utf-8",
            )

            index = GoldsetIndex(goldset_path=str(goldset_path), index_path=tmpdir)

            judge = MandatorySearchJudge(goldset_index=index)

            result = judge.judge(
                issue_id="test_001",
                issue_context="新しい設計パターンの導入を検討",
            )

            # Phase2Decisionが返ること
            assert isinstance(result, Phase2Decision)
            # 類似検索が実行されていること
            assert result.similar_search is not None
            # 判断が含まれること
            assert result.decision is not None

    def test_output_format(self):
        """出力フォーマットが正しいこと."""
        with TemporaryDirectory() as tmpdir:
            goldset_path = Path(tmpdir) / "goldset.jsonl"
            goldset_path.write_text(
                '{"context":"テスト","decision":"accept","scores":{},"reason":"理由","outcome":"結果"}\n',
                encoding="utf-8",
            )

            index = GoldsetIndex(goldset_path=str(goldset_path), index_path=tmpdir)

            judge = MandatorySearchJudge(goldset_index=index)
            result = judge.judge("test", "テスト判断")

            output = result.format_full_output()

            # 必須セクションが含まれること
            assert "類似判断" in output or "今回の判断" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
