# JARVIS Research OS チュートリアル

> はじめての体系的文献レビュー

---

## 🎯 このチュートリアルで学ぶこと

1. 論文の検索と収集
2. Active Learning によるスクリーニング
3. 証拠レベルの評価
4. 結果のエクスポート

---

## 📋 事前準備

```bash
# インストール
pip install jarvis-research-os

# または開発版
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline
pip install -e .
```

---

## Step 1: 論文の検索

### PubMed から検索

```python
from jarvis_core.sources import PubMedClient

client = PubMedClient()
papers = client.search(
    query="CD73 immunotherapy cancer",
    max_results=100
)

print(f"Found {len(papers)} papers")

# JSONL として保存
import json
with open("papers.jsonl", "w") as f:
    for paper in papers:
        f.write(json.dumps(paper.to_dict(), ensure_ascii=False) + "\n")
```

### 既存の参照文献をインポート

```bash
# RIS ファイルからインポート
jarvis import --format ris --input refs.ris --output papers.jsonl

# BibTeX からインポート
jarvis import --format bibtex --input refs.bib --output papers.jsonl
```

---

## Step 2: Active Learning スクリーニング

効率的に関連論文を選別します。

### CLI を使用

```bash
jarvis screen --input papers.jsonl --output screened.jsonl --target-recall 0.95
```

対話的にラベル付け：
```
[1234567]
Title: A randomized controlled trial of...
Abstract: Methods: We conducted...

Relevant? (y/n/q): y

--- Iteration 1 ---
Labeled: 10/100
Relevant found: 3
Estimated recall: 78.5%
```

### Python API を使用

```python
from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

config = ALConfig(
    batch_size=10,
    target_recall=0.95,
    budget_ratio=0.3,  # 最大30%のラベリングで停止
)

engine = ActiveLearningEngine(config)
engine.initialize(paper_features)  # {paper_id: [features]}

while not engine.should_stop():
    to_review = engine.get_next_query()
    
    for paper_id in to_review:
        # ユーザーがラベル付け（1=関連, 0=非関連）
        label = get_user_decision(paper_id)
        engine.update(paper_id, label)

stats = engine.get_stats()
print(f"Work saved: {1 - stats.labeled_instances/stats.total_instances:.0%}")
```

---

## Step 3: 証拠レベル評価

各論文の証拠レベルを評価します。

```python
from jarvis_core.evidence import grade_evidence

for paper in relevant_papers:
    grade = grade_evidence(
        title=paper["title"],
        abstract=paper["abstract"]
    )
    
    print(f"• {paper['title'][:50]}...")
    print(f"  Level: {grade.level.value} ({grade.level.description})")
    print(f"  Confidence: {grade.confidence:.0%}")
```

**出力例:**
```
• A randomized controlled trial of new treatment...
  Level: 1b (Individual RCT)
  Confidence: 92%

• Systematic review of clinical outcomes...
  Level: 1a (Systematic review of RCTs)
  Confidence: 88%
```

---

## Step 4: 矛盾の検出

論文間の矛盾する主張を検出します。

```python
from jarvis_core.contradiction import Claim, ContradictionDetector

detector = ContradictionDetector()

claims = [
    Claim("1", "Treatment X improves survival by 50%", "Paper A"),
    Claim("2", "Treatment X shows no significant effect", "Paper B"),
]

# すべてのペアをチェック
for i, claim_a in enumerate(claims):
    for claim_b in claims[i+1:]:
        result = detector.detect(claim_a, claim_b)
        if result.is_contradictory:
            print(f"⚠️ Contradiction found!")
            print(f"  {claim_a.paper_id}: {claim_a.text}")
            print(f"  {claim_b.paper_id}: {claim_b.text}")
```

---

## Step 5: PRISMA フロー生成

PRISMA 2020 準拠のフローチャートを生成します。

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

# SVG として保存
svg = generate_prisma_flow(data, format="svg")
with open("prisma_flow.svg", "w") as f:
    f.write(svg)

# Mermaid コードとして取得
mermaid = generate_prisma_flow(data, format="mermaid")
print(mermaid)
```

---

## Step 6: 結果のエクスポート

### BibTeX としてエクスポート

```bash
jarvis export --format bibtex --input screened.jsonl --output refs.bib
```

### RIS としてエクスポート

```bash
jarvis export --format ris --input screened.jsonl --output refs.ris
```

---

## 🎉 完成！

これで体系的文献レビューの基本的なワークフローが完了しました。

### 次のステップ

- [API リファレンス](api_reference.md) で詳細な API を確認
- [トラブルシューティング](troubleshooting_guide.md) で問題解決
- [User Guide](user_guide.md) で高度な機能を学ぶ

---

© 2026 JARVIS Team - MIT License
