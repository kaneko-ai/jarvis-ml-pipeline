# JARVIS Code Style Rules

このプロジェクトで常に適用されるコーディング規約です。

## インポート順序

以下の順序でインポートを記述する:
1. 標準ライブラリ（os, sys, re, typing等）
2. サードパーティライブラリ（pandas, numpy, requests等）
3. jarvis_core内部モジュール
4. jarvis_web, jarvis_tools

各グループ間は空行で区切る。

```python
# 正しい例
import os
import re
from typing import Optional, List

import pandas as pd
import requests

from jarvis_core.evidence import grade_evidence
from jarvis_core.citation import extract_citation_contexts
```

## 型ヒント

- すべての公開関数・メソッドには型ヒントを付ける
- `Optional`を使用する場合は`None`のデフォルト値も設定する
- 複雑な型は`typing`モジュールを使用する

```python
# 正しい例
def process_paper(
    title: str,
    abstract: str,
    keywords: Optional[List[str]] = None,
) -> EvidenceGrade:
    pass
```

## docstring形式

Google形式のdocstringを使用する:

```python
def grade_evidence(title: str, abstract: str) -> EvidenceGrade:
    """論文のエビデンスレベルを判定する。
    
    CEBMエビデンスレベルに基づいて、論文のタイトルと
    アブストラクトから研究タイプを判定する。
    
    Args:
        title: 論文タイトル
        abstract: アブストラクト
        
    Returns:
        EvidenceGrade: 判定結果（level, confidence, reasoning）
        
    Raises:
        ValueError: titleまたはabstractが空の場合
        
    Example:
        >>> result = grade_evidence("RCT of Drug X", "Methods: randomized...")
        >>> print(result.level)
        EvidenceLevel.LEVEL_1B
    """
    pass
```

## エラーハンドリング

- 外部API呼び出しは必ずtry-exceptで囲む
- 具体的な例外クラスをキャッチする（bare exceptは禁止）
- カスタム例外は`jarvis_core/exceptions.py`に定義する

```python
# 正しい例
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.Timeout:
    logger.warning(f"Request timeout: {url}")
    return None
except requests.HTTPError as e:
    logger.error(f"HTTP error: {e}")
    raise APIError(f"Failed to fetch: {url}") from e
```

## 命名規則

- クラス名: PascalCase（例: `EvidenceGrader`）
- 関数・メソッド名: snake_case（例: `grade_evidence`）
- 定数: UPPER_SNAKE_CASE（例: `MAX_RESULTS`）
- プライベートメソッド: _で始める（例: `_calculate_score`）

## ファイル構成

各Pythonファイルは以下の順序で構成する:
1. モジュールdocstring
2. `__future__`インポート（必要な場合）
3. 標準ライブラリのインポート
4. サードパーティのインポート
5. ローカルのインポート
6. 定数定義
7. クラス定義
8. 関数定義
9. `if __name__ == "__main__":` ブロック（必要な場合）

## フォーマッタ・リンター

このプロジェクトでは以下のツールを使用:
- black: コードフォーマット（line-length=100）
- ruff: リンティング
- mypy: 型チェック

コード作成後は以下を実行して確認:
```bash
uv run black .
uv run ruff check .
uv run mypy jarvis_core/
```
