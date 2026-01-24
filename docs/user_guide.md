# JARVIS Research OS ユーザーガイド

> Authority: REFERENCE (Level 2, Non-binding)


> AI駆動の体系的文献レビュー支援システム

## 目次

1. [はじめに](#はじめに)
2. [インストール](#インストール)
3. [基本的な使い方](#基本的な使い方)
4. [機能別ガイド](#機能別ガイド)
5. [設定](#設定)
6. [トラブルシューティング](#トラブルシューティング)

---

## はじめに

JARVIS Research OSは、研究者が体系的文献レビューを効率的に行うためのAI支援ツールです。

### 主な機能

| 機能 | 説明 |
|------|------|
| **証拠グレーディング** | Oxford CEBM基準（1a-5）での研究エビデンス評価 |
| **引用分析** | Support/Contrast/Mention分類で引用関係を可視化 |
| **矛盾検出** | 論文間の矛盾する主張を自動検出 |
| **PRISMAフロー** | PRISMA 2020準拠のフローチャート生成 |
| **Active Learning** | 効率的なスクリーニングのための能動学習 |
| **オフラインモード** | ネットワークなしでも動作 |

---

## インストール

### 方法1: pip（推奨）

```bash
pip install jarvis-research-os

# オプション機能をインストール（推奨）
pip install "jarvis-research-os[all]"

# 個別の機能をインストールする場合
pip install "jarvis-research-os[ml,pdf,llm]"
```

### 方法2: ソースから

```bash
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline
pip install -e .
```

### 方法3: Docker

```bash
docker pull kaneko-ai/jarvis-research-os
docker run -it jarvis-research-os --help
```

---

## CLI リファレンス

JARVISは統合CLI `jarvis` を提供します。

```bash
# ヘルプを表示
jarvis --help

# タスクの実行
jarvis run --goal "がん免疫療法の最新動向を調査"

# 論文検索インデックスの構築
jarvis build-index --query "cancer immunotherapy" --max-papers 50

# Active Learningによるスクリーニング
jarvis screen --input papers.jsonl --output labeled.jsonl

# 参考文献のインポート (BibTeX/RIS/Zotero)
jarvis import --format bibtex --input refs.bib --output papers.jsonl

# 参考文献のエクスポート (PRISMAフロー図など)
jarvis export --format prisma --input papers.jsonl --output prisma.svg
```

---

## 基本的な使い方

### 論文検索

```python
from jarvis_core.sources import ArxivClient, CrossrefClient

# arXivから検索
arxiv = ArxivClient()
papers = arxiv.search("machine learning cancer diagnosis", max_results=10)

for paper in papers:
    print(f"• {paper.title} ({paper.year})")
```

### 証拠レベル評価

```python
from jarvis_core.evidence import grade_evidence

grade = grade_evidence(
    title="A randomized controlled trial of...",
    abstract="Methods: We conducted a double-blind RCT with 500 patients..."
)

print(f"証拠レベル: {grade.level.value}")
print(f"説明: {grade.level.description}")
print(f"信頼度: {grade.confidence:.0%}")
```

### 引用分析

```python
from jarvis_core.citation import extract_citation_contexts, classify_citation_stance

# 引用コンテキストを抽出
text = """
Previous work [1] established the baseline. However, unlike [2], 
our method shows improved results. We follow the approach of [3].
"""

contexts = extract_citation_contexts(text, paper_id="my_paper")

for ctx in contexts:
    stance = classify_citation_stance(ctx.get_full_context())
    print(f"引用 {ctx.citation_marker}: {stance.stance.value}")
```

### 矛盾検出

```python
from jarvis_core.contradiction import Claim, ContradictionDetector

detector = ContradictionDetector()

claim_a = Claim(
    claim_id="1",
    text="Treatment X increases patient survival by 50%",
    paper_id="paper_A"
)
claim_b = Claim(
    claim_id="2",
    text="Treatment X decreases patient survival by 10%",
    paper_id="paper_B"
)

result = detector.detect(claim_a, claim_b)

if result.is_contradictory:
    print(f"矛盾検出: {result.contradiction_type.value}")
    print(f"証拠: {result.explanation}")
```

### PRISMAフロー図生成

```python
from jarvis_core.prisma import PRISMAData, generate_prisma_flow

data = PRISMAData(
    records_from_databases=1500,
    records_from_registers=200,
    duplicates_removed=300,
    records_screened=1400,
    records_excluded_screening=1000,
    reports_assessed=400,
    reports_excluded=350,
    studies_included=50,
)

# Mermaidコードを生成
mermaid = generate_prisma_flow(data, format="mermaid")
print(mermaid)

# SVGとして保存
svg = generate_prisma_flow(data, format="svg")
with open("prisma_flow.svg", "w") as f:
    f.write(svg)
```

---

## 機能別ガイド

### ハイブリッド検索

密ベクトル（Sentence Transformers）と疎ベクトル（BM25）を組み合わせた高精度検索。

```python
from jarvis_core.embeddings import HybridSearch

search = HybridSearch()

# ドキュメントをインデックス
docs = [
    {"id": "1", "text": "Machine learning in healthcare..."},
    {"id": "2", "text": "Cancer diagnosis using AI..."},
]
search.index(docs)

# 検索
results = search.search("AI medical diagnosis", k=5)
```

### 論文スコアリング

複数のシグナルを統合した論文品質スコア。

```python
from jarvis_core.paper_scoring import calculate_paper_score

score = calculate_paper_score(
    paper_id="paper_A",
    evidence_level=2,      # レベル2証拠
    support_count=15,      # 支持引用数
    contrast_count=3,      # 反論引用数
    publication_year=2023,
    journal_impact_factor=8.5,
)

print(f"総合スコア: {score.overall_score:.2f}")
print(f"グレード: {score.grade}")
```

### Active Learning

効率的な論文スクリーニング。

```python
from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

config = ALConfig(
    batch_size=10,
    target_recall=0.95,
    budget_ratio=0.3,
)

engine = ActiveLearningEngine(config)
engine.initialize(instances)  # 特徴ベクトルの辞書

while not engine.should_stop():
    # 次にラベル付けすべきインスタンスを取得
    to_label = engine.get_next_query()
    
    # ユーザーがラベル付け
    for instance_id in to_label:
        label = get_user_label(instance_id)  # 1=関連, 0=非関連
        engine.update(instance_id, label)

print(f"ラベル付け数: {engine.get_stats().labeled_instances}")
print(f"推定再現率: {engine.get_stats().estimated_recall:.0%}")
```

---

## 設定

`config.yaml`で設定をカスタマイズ：

```yaml
# 検索設定
search:
  default_sources:
    - pubmed
    - arxiv
    - crossref
  max_results: 100
  timeout: 30

# 埋め込み設定
embeddings:
  model: all-MiniLM-L6-v2  # または allenai/specter2
  device: auto  # auto, cpu, cuda
  batch_size: 32

# 証拠グレーディング設定
evidence:
  use_llm: false  # LLM分類器を使用
  ensemble_strategy: weighted_average
  rule_weight: 0.4
  llm_weight: 0.6

# オフラインモード
offline:
  enabled: true
  sync_on_connect: true
  cache_dir: ~/.jarvis/cache

# Active Learning
active_learning:
  batch_size: 10
  initial_samples: 20
  target_recall: 0.95
  max_iterations: 100
```

---

## トラブルシューティング

### よくある問題

#### `sentence-transformers not installed`

```bash
pip install sentence-transformers
```

#### オフラインモードで動作避ける

ネットワーク検出を無効化：

```python
from jarvis_core.network import NetworkDetector
detector = NetworkDetector()
detector.disable()  # オフラインモードを強制
```

#### メモリ不足

バッチサイズを小さくする：

```yaml
embeddings:
  batch_size: 8  # デフォルト32から削減
```

### ログの有効化

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## サポート

- **Issues**: https://github.com/kaneko-ai/jarvis-ml-pipeline/issues
- **Discussions**: https://github.com/kaneko-ai/jarvis-ml-pipeline/discussions

---

© 2026 JARVIS Team - MIT License
