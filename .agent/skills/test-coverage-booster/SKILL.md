---
name: test-coverage-booster
description: テストカバレッジを分析し、不足しているテストを自動生成します。「カバレッジを上げて」「このモジュールのテストを追加して」「テストが足りない部分を補完して」などの依頼時に使用してください。
---

# Test Coverage Booster Skill

## 目的
jarvis_coreのテストカバレッジを50%以上に維持・向上させる。

## 手順

### Step 1: カバレッジ分析
以下のコマンドを実行してカバレッジレポートを取得する:
```bash
uv run pytest --cov=jarvis_core --cov-report=term-missing -q
```

### Step 2: 不足箇所の特定
カバレッジレポートから以下を確認:
- カバレッジが50%未満のモジュール
- `Missing`列に表示される未テスト行番号

### Step 3: テスト生成の優先順位
以下の順序でテストを作成する:
1. `__all__`に含まれる公開API（関数・クラス）
2. 例外処理・エラーハンドリングパス
3. 境界値・エッジケース
4. 分岐条件（if/else）

### Step 4: テストファイルの配置
- テストファイルは `tests/` 配下に配置
- ファイル名は `test_<モジュール名>.py` 形式
- 既存のテストファイルがあれば追記

### Step 5: テスト命名規則
```python
def test_<機能名>_<条件>_<期待結果>():
    """テストの説明"""
    pass

# 例:
def test_grade_evidence_rct_abstract_returns_level_1b():
    """RCTを含むアブストラクトがエビデンスレベル1bを返すことを確認"""
    pass
```

### Step 6: テスト実行と確認
テスト作成後、以下を実行して確認:
```bash
uv run pytest tests/test_<作成したファイル>.py -v
```

## テストテンプレート

```python
"""<モジュール名>のテスト"""
import pytest
from jarvis_core.<module> import <対象クラス・関数>


class Test<クラス名>:
    """<クラス名>のテストクラス"""

    def test_初期化_正常系(self):
        """正常な初期化を確認"""
        instance = <クラス名>()
        assert instance is not None

    def test_メソッド名_正常な入力_期待される出力(self):
        """正常な入力で期待される出力を返すことを確認"""
        instance = <クラス名>()
        result = instance.<メソッド>(<入力>)
        assert result == <期待値>

    def test_メソッド名_不正な入力_例外発生(self):
        """不正な入力で適切な例外が発生することを確認"""
        instance = <クラス名>()
        with pytest.raises(<例外クラス>):
            instance.<メソッド>(<不正な入力>)


def test_関数名_正常系():
    """関数の正常系テスト"""
    result = <関数名>(<入力>)
    assert result == <期待値>
```

## 制約
- pytestの規約に従う（test_*.py, Test*クラス, test_*メソッド）
- 共通fixtureは `tests/conftest.py` に配置
- 外部APIはモック化する（requestsなど）
- モックは最小限に抑え、実際の動作確認を優先
- 1つのテスト関数は1つの振る舞いのみをテスト
