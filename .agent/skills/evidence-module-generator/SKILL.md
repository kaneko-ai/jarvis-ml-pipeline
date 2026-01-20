---
name: evidence-module-generator
description: CEBMエビデンスレベル分類用の新しいグレーダーモジュールを生成します。「新しい研究タイプのグレーダーを作成して」「RCT検出ロジックを追加して」「エビデンス分類を拡張して」などの依頼時に使用してください。
---

# Evidence Module Generator Skill

## 目的
jarvis_core/evidence/配下に新しいエビデンス分類モジュールを作成する。

## CEBMエビデンスレベル一覧

| レベル | 説明 |
|--------|------|
| 1a | システマティックレビュー（RCTの） |
| 1b | 個々のRCT（狭い信頼区間） |
| 2a | システマティックレビュー（コホート研究の） |
| 2b | 個々のコホート研究 |
| 3a | システマティックレビュー（症例対照研究の） |
| 3b | 個々の症例対照研究 |
| 4 | 症例集積研究 |
| 5 | 専門家の意見 |

## 手順

### Step 1: 要件の確認
ユーザーの要求から以下を特定:
- 対象とする研究タイプ（RCT, メタ分析, コホート等）
- 検出に使用するキーワード・パターン
- 期待されるエビデンスレベル

### Step 2: モジュール構造の決定
```
jarvis_core/evidence/
├── __init__.py
├── grader.py          # メインのグレーダー
├── levels.py          # EvidenceLevelのenum定義
├── patterns.py        # 検出パターン定義
└── <新モジュール>.py  # 新しく作成するモジュール
```

### Step 3: 基本クラス構造
```python
"""<研究タイプ>のエビデンスグレーダー"""
from dataclasses import dataclass
from typing import Optional
import re

from .levels import EvidenceLevel


@dataclass
class <Type>GradeResult:
    """グレーディング結果"""
    level: EvidenceLevel
    confidence: float  # 0.0-1.0
    reasoning: str
    matched_patterns: list[str]


class <Type>Grader:
    """<研究タイプ>のエビデンスレベルを判定するグレーダー
    
    CEBMエビデンスレベルに基づいて、論文のタイトルと
    アブストラクトから研究タイプを判定し、適切なレベルを返す。
    """

    # 検出パターン
    PATTERNS = {
        "pattern_name": [
            r"正規表現パターン1",
            r"正規表現パターン2",
        ],
    }

    def __init__(self, use_llm: bool = False):
        """初期化
        
        Args:
            use_llm: LLMを使用した高精度判定を行うかどうか
        """
        self.use_llm = use_llm

    def grade(self, title: str, abstract: str) -> <Type>GradeResult:
        """エビデンスレベルを判定する
        
        Args:
            title: 論文タイトル
            abstract: アブストラクト
            
        Returns:
            グレーディング結果
        """
        text = f"{title} {abstract}".lower()
        matched = self._find_patterns(text)
        
        level = self._determine_level(matched)
        confidence = self._calculate_confidence(matched)
        reasoning = self._generate_reasoning(matched, level)
        
        return <Type>GradeResult(
            level=level,
            confidence=confidence,
            reasoning=reasoning,
            matched_patterns=matched,
        )

    def _find_patterns(self, text: str) -> list[str]:
        """パターンマッチングを実行"""
        matched = []
        for name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matched.append(name)
                    break
        return matched

    def _determine_level(self, matched: list[str]) -> EvidenceLevel:
        """マッチしたパターンからレベルを決定"""
        # 実装: マッチしたパターンに基づいてレベルを返す
        raise NotImplementedError

    def _calculate_confidence(self, matched: list[str]) -> float:
        """信頼度スコアを計算"""
        if not matched:
            return 0.0
        # マッチしたパターン数に基づいて信頼度を計算
        return min(len(matched) * 0.3, 1.0)

    def _generate_reasoning(self, matched: list[str], level: EvidenceLevel) -> str:
        """判定理由を生成"""
        if not matched:
            return "No matching patterns found"
        return f"Matched patterns: {', '.join(matched)} -> {level.value}"
```

### Step 4: テストの作成
`tests/evidence/test_<新モジュール>.py` を作成:
```python
"""<新モジュール>のテスト"""
import pytest
from jarvis_core.evidence.<新モジュール> import <Type>Grader
from jarvis_core.evidence.levels import EvidenceLevel


class Test<Type>Grader:
    """<Type>Graderのテスト"""

    @pytest.fixture
    def grader(self):
        return <Type>Grader()

    def test_grade_典型的な入力_正しいレベル(self, grader):
        """典型的な入力で正しいレベルを返す"""
        result = grader.grade(
            title="典型的なタイトル",
            abstract="典型的なアブストラクト"
        )
        assert result.level == EvidenceLevel.LEVEL_XX

    def test_grade_パターンなし_レベル5(self, grader):
        """パターンにマッチしない場合はレベル5を返す"""
        result = grader.grade(
            title="Generic title",
            abstract="Generic abstract"
        )
        assert result.level == EvidenceLevel.LEVEL_5
```

### Step 5: __init__.pyへの追加
`jarvis_core/evidence/__init__.py` にエクスポートを追加:
```python
from .<新モジュール> import <Type>Grader, <Type>GradeResult

__all__ = [
    # 既存のエクスポート...
    "<Type>Grader",
    "<Type>GradeResult",
]
```

## 制約
- 既存のEvidenceLevel enumとの互換性を維持すること
- 必ず`grade()`メソッドを実装すること
- docstringにエビデンスレベルの判定基準を明記すること
- 新しいパターン追加時は必ずテストケースを同時に追加すること
- confidence scoreは0.0-1.0の範囲で返すこと
