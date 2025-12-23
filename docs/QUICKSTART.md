# JARVIS Quickstart Guide

5分でJARVISを使い始めましょう！

## 1. インストール

```bash
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline
cd jarvis-ml-pipeline
pip install -r requirements.lock
```

## 2. 基本的な使い方

### 仮説生成

```python
from jarvis_core.scientist import HypothesisGenerator

hg = HypothesisGenerator()
for h in hg.generate_hypotheses("cancer treatment", n=3):
    print(f"💡 {h['text']}")
```

### 論文検索

```python
from jarvis_core.integrations.pubmed import get_pubmed_client

client = get_pubmed_client()
papers = client.search("machine learning healthcare", max_results=5)
for p in papers:
    print(f"📄 {p['title']}")
```

### タンパク質構造

```python
from jarvis_core.protein import AlphaFoldIntegration

af = AlphaFoldIntegration()
url = af.get_structure_url("P12345")["viewer_url"]
print(f"🔬 View: {url}")
```

### メタ分析

```python
from jarvis_core.advanced import MetaAnalysisBot

ma = MetaAnalysisBot()
result = ma.run_meta_analysis([
    {"effect_size": 0.5, "sample_size": 100},
    {"effect_size": 0.6, "sample_size": 150}
])
print(f"📊 Pooled effect: {result['pooled_effect_size']}")
```

## 3. ダッシュボード

ブラウザで開く:
```
https://kaneko-ai.github.io/jarvis-ml-pipeline/
```

## 4. パイプライン実行

```bash
gh workflow run research-pipelines.yml \
  -f pipeline=hypothesis \
  -f topic="cancer immunotherapy"
```

## 5. 次のステップ

- [FEATURES_300.md](FEATURES_300.md) - 全300機能ガイド
- [JARVIS_MASTER.md](JARVIS_MASTER.md) - アーキテクチャ
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - デプロイ方法
