# JARVIS Research OS API リファレンス

> Authority: REFERENCE (Level 2, Non-binding)


> 完全な API ドキュメンテーション | v5.1.0

---

## 目次

1. [CLI コマンド](#cli-コマンド)
2. [Evidence Grading](#evidence-grading)
3. [Citation Analysis](#citation-analysis)
4. [Contradiction Detection](#contradiction-detection)
5. [PRISMA Flow](#prisma-flow)
6. [Active Learning](#active-learning)
7. [Embeddings](#embeddings)
8. [Sources](#sources)

---

## CLI コマンド

### `jarvis run`

タスクを実行します。

```bash
jarvis run --goal "CD73 immunotherapy survey" --pipeline configs/pipelines/e2e_oa10.yml
```

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--goal` | str | - | タスクの目標 |
| `--task-file` | str | - | タスク JSON ファイル |
| `--category` | str | generic | カテゴリ（paper_survey, thesis, job_hunting, generic） |
| `--pipeline` | str | e2e_oa10.yml | パイプライン YAML |
| `--json` | flag | - | JSON 出力 |

### `jarvis screen`

Active Learning による論文スクリーニング。

```bash
jarvis screen --input papers.jsonl --output screened.jsonl --target-recall 0.95
```

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--input` | str | 必要 | 入力 JSONL |
| `--output` | str | 必要 | 出力 JSONL |
| `--batch-size` | int | 10 | バッチサイズ |
| `--target-recall` | float | 0.95 | 目標再現率 |
| `--budget-ratio` | float | 0.3 | 予算比率 |
| `--auto` | flag | - | 自動ラベリング |

### `jarvis import`

RIS/BibTeX/Zotero からインポート。

```bash
jarvis import --format ris --input refs.ris --output papers.jsonl
```

### `jarvis export`

RIS/BibTeX/PRISMA へエクスポート。

```bash
jarvis export --format bibtex --input papers.jsonl --output refs.bib
```

---

## Evidence Grading

### `grade_evidence()`

論文の証拠レベルを評価します。

```python
from jarvis_core.evidence import grade_evidence

result = grade_evidence(
    title="A randomized controlled trial...",
    abstract="Methods: We conducted a double-blind RCT..."
)

print(result.level)        # EvidenceLevel.LEVEL_1B
print(result.confidence)   # 0.85
```

### クラス: `EvidenceLevel`

| レベル | 説明 |
|--------|------|
| LEVEL_1A | 系統的レビュー（均質な RCT） |
| LEVEL_1B | 個別の RCT |
| LEVEL_2A | 系統的レビュー（コホート） |
| LEVEL_2B | 個別のコホート研究 |
| LEVEL_3A | 系統的レビュー（症例対照） |
| LEVEL_3B | 個別の症例対照研究 |
| LEVEL_4 | 症例シリーズ |
| LEVEL_5 | 専門家意見 |

---

## Citation Analysis

### `extract_citation_contexts()`

引用コンテキストを抽出します。

```python
from jarvis_core.citation import extract_citation_contexts

contexts = extract_citation_contexts(text, paper_id="my_paper")
```

### `classify_citation_stance()`

引用のスタンスを分類します。

```python
from jarvis_core.citation import classify_citation_stance

stance = classify_citation_stance("Previous work [1] supports this...")
print(stance.stance)  # CitationStance.SUPPORT
```

---

## Contradiction Detection

### `ContradictionDetector`

矛盾を検出します。

```python
from jarvis_core.contradiction import Claim, ContradictionDetector

detector = ContradictionDetector()

claim_a = Claim(claim_id="1", text="X increases Y", paper_id="A")
claim_b = Claim(claim_id="2", text="X decreases Y", paper_id="B")

result = detector.detect(claim_a, claim_b)
print(result.is_contradictory)  # True
```

---

## PRISMA Flow

### `generate_prisma_flow()`

PRISMA 2020 フローチャートを生成します。

```python
from jarvis_core.prisma import PRISMAData, generate_prisma_flow

data = PRISMAData(
    records_from_databases=1500,
    records_screened=1400,
    studies_included=50,
)

mermaid = generate_prisma_flow(data, format="mermaid")
svg = generate_prisma_flow(data, format="svg")
```

---

## Active Learning

### `ActiveLearningEngine`

効率的な論文スクリーニング。

```python
from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

config = ALConfig(batch_size=10, target_recall=0.95)
engine = ActiveLearningEngine(config)
engine.initialize(instances)

while not engine.should_stop():
    to_label = engine.get_next_query()
    for instance_id in to_label:
        engine.update(instance_id, label)
```

---

## Embeddings

### `HybridSearch`

ハイブリッド検索（密＋疎ベクトル）。

```python
from jarvis_core.embeddings import HybridSearch

search = HybridSearch()
search.index(documents)
results = search.search("AI medical diagnosis", k=10)
```

---

## Sources

### `ArxivClient`

arXiv API クライアント。

```python
from jarvis_core.sources import ArxivClient

client = ArxivClient()
papers = client.search("machine learning", max_results=20)
```

### `CrossrefClient`

Crossref API クライアント。

```python
from jarvis_core.sources import CrossrefClient

client = CrossrefClient()
paper = client.get_by_doi("10.1038/s41586-020-2649-2")
```

---

© 2026 JARVIS Team - MIT License

---

## New Subcommands (2026-02-16)

### `jarvis papers tree`

```bash
jarvis papers tree --id arxiv:1234.5678 --depth 2 --max-per-level 50 --out logs/runs --out-run auto
```

Outputs:
- `logs/runs/<run_id>/paper_graph/tree/graph.json`
- `logs/runs/<run_id>/paper_graph/tree/tree.md`
- `logs/runs/<run_id>/paper_graph/tree/tree.mermaid.md`
- `logs/runs/<run_id>/paper_graph/tree/summary.md`

### `jarvis papers map3d`

```bash
jarvis papers map3d --id arxiv:1234.5678 --k 30 --out logs/runs --out-run auto
```

Outputs:
- `logs/runs/<run_id>/paper_graph/map3d/map_points.json`
- `logs/runs/<run_id>/paper_graph/map3d/map.md`
- `logs/runs/<run_id>/paper_graph/map3d/map.html` (optional)

### `jarvis harvest watch` / `jarvis harvest work`

```bash
jarvis harvest watch --source pubmed --since-hours 6 --budget "max_items=200,max_minutes=30,max_requests=400" --out logs/runs --out-run auto
jarvis harvest work  --budget "max_items=200,max_minutes=30,max_requests=400" --out logs/runs --out-run <same_run_id>
```

Outputs:
- `logs/runs/<run_id>/harvest/queue.jsonl`
- `logs/runs/<run_id>/harvest/items/`
- `logs/runs/<run_id>/harvest/stats.json`
- `logs/runs/<run_id>/harvest/report.md`

Queue persistence scope:
- `harvest/queue.jsonl` is **run-scoped** (`logs/runs/{run_id}/harvest/queue.jsonl`)

### `jarvis radar run`

```bash
jarvis radar run --source arxiv --query "immunometabolism PD-1" --since-days 2 --out logs/runs --out-run auto
```

Outputs:
- `logs/runs/<run_id>/radar/radar_findings.json`
- `logs/runs/<run_id>/radar/upgrade_proposals.md`

### `jarvis collect papers` / `jarvis collect drive-sync`

```bash
jarvis collect papers --query "cd73 immunotherapy" --max 50 --oa-only true --out logs/runs --out-run auto
jarvis collect drive-sync --run-id <run_id> --drive-folder <folder_id_or_path>
```

Outputs:
- `logs/runs/<run_id>/collector/papers.json`
- `logs/runs/<run_id>/collector/pdfs/`
- `logs/runs/<run_id>/collector/bibtex/`
- `logs/runs/<run_id>/collector/report.md`

### `jarvis market propose`

```bash
jarvis market propose --input-run <run_id> --market-data-dir market_data --out logs/runs --out-run auto
```

Outputs:
- `logs/runs/<run_id>/market/proposals.json`
- `logs/runs/<run_id>/market/proposals_deck.md`
