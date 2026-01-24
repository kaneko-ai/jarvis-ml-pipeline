# JARVIS Research OS トラブルシューティングガイド

> Authority: REFERENCE (Level 2, Non-binding)


> よくある問題と解決策

---

## 目次

1. [インストールの問題](#インストールの問題)
2. [依存関係エラー](#依存関係エラー)
3. [LLM/埋め込みの問題](#llm埋め込みの問題)
4. [API 関連の問題](#api-関連の問題)
5. [パフォーマンスの問題](#パフォーマンスの問題)
6. [デバッグ方法](#デバッグ方法)

---

## インストールの問題

### `pip install` が失敗する

**症状:**
```
ERROR: Could not build wheels for XXX
```

**解決策:**
```bash
# ビルドツールを更新
pip install --upgrade pip setuptools wheel

# 再インストール
pip install jarvis-research-os
```

### Python バージョンエラー

**症状:**
```
Python 3.9 is not supported
```

**解決策:**
```bash
# Python 3.10以上が必要
python --version

# pyenv で管理している場合
pyenv install 3.11
pyenv local 3.11
```

---

## 依存関係エラー

### `sentence-transformers not installed`

**解決策:**
```bash
pip install sentence-transformers

# または全ての依存関係をインストール
pip install jarvis-research-os[all]
```

### `lightgbm` のビルドエラー

**Windows の場合:**
```bash
# Visual C++ Build Tools が必要
pip install lightgbm --no-build-isolation
```

**macOS の場合:**
```bash
brew install libomp
pip install lightgbm
```

---

## LLM/埋め込みの問題

### Ollama に接続できない

**症状:**
```
Connection refused: http://localhost:11434
```

**解決策:**
```bash
# Ollama が起動しているか確認
ollama list

# 起動していない場合
ollama serve

# モデルをダウンロード
ollama pull llama3.2
```

### CUDA メモリ不足

**症状:**
```
CUDA out of memory
```

**解決策:**
```python
# CPU を使用
from jarvis_core.embeddings import SentenceTransformerEmbedding

embedder = SentenceTransformerEmbedding(device="cpu")
```

または設定ファイルで:
```yaml
# config.yaml
embeddings:
  device: cpu
  batch_size: 8  # バッチサイズを削減
```

---

## API 関連の問題

### PubMed のレート制限

**症状:**
```
HTTP 429: Too Many Requests
```

**解決策:**
```python
from jarvis_core.sources import PubMedClient

# API キーを設定してレート制限を緩和
client = PubMedClient(api_key="your_ncbi_api_key")
```

API キーは [NCBI](https://www.ncbi.nlm.nih.gov/account/settings/) で取得できます。

### Semantic Scholar のタイムアウト

**症状:**
```
ReadTimeout: Read timed out.
```

**解決策:**
```python
from jarvis_core.sources import SemanticScholarClient

client = SemanticScholarClient(timeout=60)  # タイムアウトを延長
```

---

## パフォーマンスの問題

### 検索が遅い

**解決策:**

1. **インデックスを事前構築:**
```bash
jarvis build-index --query "your topic" --max-papers 1000
```

2. **キャッシュを有効化:**
```python
from jarvis_core.cache import enable_cache
enable_cache("~/.jarvis/cache")
```

### メモリ使用量が多い

**解決策:**
```yaml
# config.yaml
embeddings:
  batch_size: 8  # デフォルト32から削減
  
active_learning:
  batch_size: 5  # デフォルト10から削減
```

---

## デバッグ方法

### ログの有効化

```python
import logging

# デバッグレベルのログを表示
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
```

### 特定モジュールのログ

```python
import logging

# 特定のモジュールだけ詳細ログ
logging.getLogger("jarvis_core.evidence").setLevel(logging.DEBUG)
logging.getLogger("jarvis_core.sources").setLevel(logging.DEBUG)
```

### 実行トレースの確認

```bash
# 最新の実行結果を確認
jarvis show-run

# 特定の実行を確認
jarvis show-run --run-id abc123 --json
```

---

## よくある質問

### Q: オフラインで動作しますか？

**A:** はい。ローカル LLM（Ollama）とローカル埋め込みを使用することで、完全オフラインで動作します。

```bash
jarvis run --offline --goal "analyze local papers"
```

### Q: 日本語の論文を処理できますか？

**A:** はい。多言語埋め込みモデルを使用してください。

```yaml
# config.yaml
embeddings:
  model: paraphrase-multilingual-MiniLM-L12-v2
```

### Q: カスタムプラグインを追加できますか？

**A:** はい。`Plugin` 基底クラスを継承してください。

```python
from jarvis_core.plugins import Plugin, PluginRegistry

class MyPlugin(Plugin):
    NAME = "my_plugin"
    VERSION = "1.0.0"
    
    def execute(self, **kwargs):
        # カスタムロジック
        pass

# 登録
registry = PluginRegistry()
registry.register(MyPlugin)
```

---

## サポート

問題が解決避ける場合:

- **GitHub Issues**: https://github.com/kaneko-ai/jarvis-ml-pipeline/issues
- **Discussions**: https://github.com/kaneko-ai/jarvis-ml-pipeline/discussions

---

© 2026 JARVIS Team - MIT License
