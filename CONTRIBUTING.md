# Contributing to JARVIS Research OS

JARVIS Research OSへの貢献をご検討いただきありがとうございます！

## 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 開発用依存関係をインストール
pip install -e ".[dev]"

# pre-commitフックを設定
pre-commit install
```

## 開発フロー

1. **Issue確認**: 作業前に関連Issueを確認または作成
2. **ブランチ作成**: `feature/task-X.X.X-description` 形式
3. **実装**: コードを書く
4. **テスト**: `pytest` を実行
5. **Lint**: `ruff check .` と `black --check .` を実行
6. **PR作成**: テンプレートに従ってPRを作成

## ブランチ命名規則

- `feature/task-X.X.X-description`: 新機能（開発計画タスク）
- `fix/issue-XXX-description`: バグ修正
- `docs/description`: ドキュメント更新
- `refactor/description`: リファクタリング

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に従ってください。

```
feat(evidence): add LLM-based evidence scorer

- Implement EvidenceGrade enum
- Add LLMEvidenceScorer class
- Add unit tests

Closes #123
```

タイプ:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `test`: テスト
- `refactor`: リファクタリング
- `chore`: その他

## プルリクエスト

### 必須条件

- [ ] 関連Issueへのリンク
- [ ] テストが追加/更新されている
- [ ] ドキュメントが更新されている
- [ ] CI/CDが通過している
- [ ] レビュアーが指定されている

### PRテンプレート

```markdown
## 概要

[変更の概要]

## 関連Issue

Closes #XXX

## 変更内容

- [変更1]
- [変更2]

## テスト

- [ ] 単体テスト追加
- [ ] 統合テスト追加
- [ ] E2Eテスト追加

## チェックリスト

- [ ] コードがスタイルガイドに準拠
- [ ] セルフレビュー完了
- [ ] ドキュメント更新
```

## コードスタイル

### Python

- フォーマッター: Black (line-length=100)
- リンター: Ruff
- 型チェック: mypy (strict)

### 命名規則

- クラス: `PascalCase`
- 関数/変数: `snake_case`
- 定数: `UPPER_SNAKE_CASE`
- プライベート: `_prefix`

### ドキュメント

- Google スタイル docstring
- 全publicメソッドにdocstring必須

```python
def process_paper(paper: Paper, options: dict | None = None) -> ProcessedPaper:
    """論文を処理して構造化データを抽出する。
    
    Args:
        paper: 処理対象の論文
        options: 処理オプション
            - extract_figures: 図表を抽出するか (default: True)
            - extract_tables: テーブルを抽出するか (default: True)
    
    Returns:
        処理済みの論文データ
    
    Raises:
        ProcessingError: 処理中にエラーが発生した場合
    
    Example:
        >>> paper = Paper(title="Example", abstract="...")
        >>> result = process_paper(paper)
        >>> print(result.claims)
    """
```

## テスト

### テストの書き方

```python
import pytest
from jarvis_core.evidence import EvidenceScorer

class TestEvidenceScorer:
    """EvidenceScorerのテスト"""
    
    @pytest.fixture
    def scorer(self):
        return EvidenceScorer()
    
    def test_score_strong_evidence(self, scorer):
        """強い根拠のスコアリング"""
        evidence = Evidence(text="RCT with n=1000...")
        result = scorer.score(evidence)
        assert result.grade == EvidenceGrade.STRONG
    
    @pytest.mark.parametrize("text,expected", [
        ("meta-analysis shows...", EvidenceGrade.STRONG),
        ("case report of...", EvidenceGrade.WEAK),
    ])
    def test_score_various_evidence(self, scorer, text, expected):
        """様々な根拠のスコアリング"""
        evidence = Evidence(text=text)
        result = scorer.score(evidence)
        assert result.grade == expected
```

### テスト実行

```bash
# 全テスト
pytest

# 特定のテスト
pytest tests/test_evidence.py

# カバレッジ付き
pytest --cov=jarvis_core --cov-report=html

# E2Eテスト
pytest -m e2e
```

## 質問・サポート

- **バグ報告**: GitHub Issues
- **機能要望**: GitHub Issues
- **質問**: GitHub Discussions
- **セキュリティ**: security@example.com (非公開)

---

皆様の貢献をお待ちしています！
