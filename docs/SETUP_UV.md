# JARVIS環境構築（uv版）

> **重要**: 環境構築は`uv`を正式な方法とします。`pip install`の直接使用は**禁止**です。

---

## uvのインストール

### Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux / macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## プロジェクトのセットアップ

```bash
# リポジトリをclone
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline
cd jarvis-ml-pipeline

# 依存関係を完全固定でインストール
uv sync

# 開発用依存も含める場合
uv sync --dev
```

---

## 実行方法

```bash
# CLIコマンド実行
uv run python jarvis_cli.py run --goal "your query"

# テスト実行
uv run pytest tests/ -v

# 特定のスクリプト実行
uv run python examples/generate_report_with_evidence.py
```

---

## CI/CD環境での使用

GitHub Actionsでは以下のように使用します：

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.10'
    
- name: Install uv
  run: pip install uv
  
- name: Install dependencies (frozen)
  run: uv sync --frozen --dev
  
- name: Run tests
  run: uv run pytest tests/ -v
```

`--frozen`フラグは、`uv.lock`と完全に一致する依存関係のみをインストールし、再現性を保証します。

---

## 依存関係の更新

依存関係を変更する場合：

1. `pyproject.toml`を編集
2. `uv lock`を実行してlockファイルを更新
3. `uv sync`で環境に反映
4. **必ず`uv.lock`をコミット**

```bash
# pyproject.toml編集後
uv lock
uv sync
git add uv.lock pyproject.toml
git commit -m "deps: Update dependencies"
```

---

## トラブルシューティング

### lockファイルが古い警告が出る
```bash
# lockファイルを再生成
uv lock

# 環境を再同期
uv sync
```

### 依存関係の競合
```bash
# クリーンインストール
rm -rf .venv
uv sync --dev
```

---

## ルール（厳守）

- ✅ 環境構築は`uv sync`のみ使用
- ✅ 実行は`uv run`経由
- ✅ lockファイルは**必ずコミット**
- ❌ `pip install`の直接使用は禁止（例外なし）
- ❌ `requirements.txt`による管理は非推奨
