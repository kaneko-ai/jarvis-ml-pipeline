# JARVIS Test Requirements

テスト作成時に常に適用されるルールです。

## 必須要件

### 新機能追加時
- 同一PR内で対応するテストを追加すること
- 最低限のテストケース:
  - 正常系: 1つ以上
  - エラー系: 1つ以上

### カバレッジ目標
- プロジェクト全体: 50%以上（CI必須）
- 新規モジュール: 60%以上（推奨）

## テストファイルの配置

```
tests/
├── conftest.py           # 共通fixture
├── fixtures/             # テストデータ
│   ├── sample_paper.json
│   └── sample_abstract.txt
├── evidence/             # evidenceモジュールのテスト
│   ├── test_grader.py
│   └── test_levels.py
├── citation/             # citationモジュールのテスト
└── ...
```

## テスト命名規則

```python
# 関数テスト
def test_<機能名>_<条件>_<期待結果>():
    pass

# 例
def test_grade_evidence_rct_abstract_returns_level_1b():
    pass

def test_grade_evidence_empty_abstract_raises_value_error():
    pass

# クラステスト
class Test<クラス名>:
    def test_<メソッド名>_<条件>_<期待結果>(self):
        pass
```

## Fixture使用ガイドライン

共通fixtureは`tests/conftest.py`に配置:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_paper():
    """サンプル論文データ"""
    return {
        "title": "A Randomized Controlled Trial of Drug X",
        "abstract": "Methods: We conducted a double-blind RCT...",
        "authors": ["Author A", "Author B"],
    }

@pytest.fixture
def mock_api_response():
    """APIレスポンスのモック"""
    return {
        "status": "ok",
        "results": [],
    }
```

## モック使用ガイドライン

外部APIは必ずモック化する:

```python
from unittest.mock import patch, MagicMock

def test_fetch_paper_success():
    """API呼び出しが成功した場合のテスト"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"title": "Test Paper"}
    mock_response.raise_for_status = MagicMock()
    
    with patch("requests.get", return_value=mock_response):
        result = fetch_paper("12345")
        assert result["title"] == "Test Paper"
```

## パラメータ化テスト

複数の入力パターンをテストする場合:

```python
import pytest

@pytest.mark.parametrize("input_text,expected_level", [
    ("randomized controlled trial", EvidenceLevel.LEVEL_1B),
    ("systematic review", EvidenceLevel.LEVEL_1A),
    ("case report", EvidenceLevel.LEVEL_4),
    ("expert opinion", EvidenceLevel.LEVEL_5),
])
def test_grade_evidence_various_inputs(input_text, expected_level):
    result = grade_evidence(title=input_text, abstract="")
    assert result.level == expected_level
```

## テスト実行コマンド

```bash
# 全テスト実行
uv run pytest

# 特定モジュールのテスト
uv run pytest tests/evidence/ -v

# カバレッジ付き
uv run pytest --cov=jarvis_core --cov-report=term-missing

# 失敗したテストのみ再実行
uv run pytest --lf
```

## CI/CD連携

GitHub Actionsで以下が自動実行される:
- `uv run pytest`: 全テスト実行
- `--cov-fail-under=50`: カバレッジ50%未満でCI失敗

PRマージ前に必ずローカルで確認:
```bash
uv run pytest --cov=jarvis_core --cov-fail-under=50
```
