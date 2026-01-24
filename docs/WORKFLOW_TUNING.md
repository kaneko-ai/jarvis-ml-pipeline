# JARVIS Workflow チューニングガイド

> Authority: REFERENCE (Level 2, Non-binding)


PDF知見統合（LayerX/Findy/AI Builders）に基づくワークフロー自動改善ガイド。

---

## 概要

このガイドでは、JARVISのWorkflow Tuner機能について説明します。

### 3つの統合原則

1. **自動改善ループ（LayerX）**: Generator→Executor→Evaluator→Memory→Sampling
2. **ガードレール/適応度関数（Findy）**: "動いたらOK"を非推奨、Fitnessで収束
3. **主導権設計（AI Builders）**: step/hitl/durableモードで運用形を明示

---

## 主導権モード（Mode）

| モード | 説明 | 使用場面 |
|-------|------|---------|
| `step` | 状態遷移として割り込み | **MVP（推奨）**。step単位で再試行・再開可能 |
| `hitl` | 人間の判断を前提化 | 承認/修正が必要な場面 |
| `durable` | 処理内割り込み | 長時間待機、非同期処理（後で実装） |

### 選び方

- **自動化したい** → `step`
- **人間のレビューが必要** → `hitl`
- **長時間処理、外部待ち** → `durable`（将来）

---

## Fitness（適応度関数）

### 定義

| 指標 | 説明 | デフォルト重み |
|-----|------|--------------|
| `correctness` | 引用精度、スキーマ準拠 | 0.4 |
| `regression` | 前回ベストより悪化していないか | 0.2 |
| `reproducibility` | 再現性（同一入力での分散） | 0.2 |
| `cost` | 推論コスト | 0.1 |
| `latency` | 時間 | 0.1 |

### ハードゲート

Fitnessの最低条件を満たさないWorkflowは**採用不可**：

- `correctness >= 0.7`
- `regression <= 0.1`
- `reproducibility >= 0.8`
- `security == 1.0`（セキュリティ問題なし）

---

## Repeated Sampling

LayerXの「最適化不安定」対策。

### 動作

1. N本の候補を生成
2. 各候補を評価
3. ベストを採用

### コスト制御

- `n_samples`: デフォルト3
- コスト上限に近づくと自動で`n_samples`を下げる
- 最低1本は必ず生成

---

## コンテキスト爆発対策

全ログをLLMに渡すのは**非推奨**。

### ContextPackager

1. 下位K%のログだけ抽出
2. 要約して渡す
3. スコア差分表を生成
4. 回帰したケースをハイライト

---

## 回帰検知と調査手順

### 回帰が出たとき

1. **差分表を確認**: どのメトリクスが悪化したか
2. **下位ログを確認**: 何が失敗しているか
3. **再現を試みる**: 同じ入力で再実行
4. **Generatorに戻す**: 回帰したケースを優先的に見せる

---

## CLI使用方法

### ワークフロー実行

```bash
jarvis workflow:run --spec workflows/paper_meta.yaml
```

### ワークフローチューニング

```bash
jarvis workflow:tune --spec workflows/paper_meta.yaml --goldset data/gold/paper_meta.jsonl
```

> ⚠️ **重要**: `tune`は必ず`goldset`前提。goldset無しの自動改善はUnknown-Unknownを拡大させます。

---

## サンプルワークフロー定義

```yaml
workflow_id: paper_meta_analysis
mode: step
objective: PubMedからOA10本→要約→根拠行→採点

steps:
  - step_id: search
    action: tool
    tool: pubmed_search
    config:
      query: "meta-analysis cancer treatment"
      max_results: 10

  - step_id: extract
    action: tool
    tool: claim_extractor

  - step_id: evaluate
    action: evaluator
    requires_approval: false

fitness:
  correctness: 0.4
  regression: 0.2
  reproducibility: 0.2
  cost: 0.1
  latency: 0.1

budgets:
  max_tokens: 100000
  max_cost: 10.0
  max_iters: 10
  n_samples: 3

goldset: data/gold/paper_meta.jsonl
```

---

## DoD（Definition of Done）との連携

| DoD項目 | Workflow対応 |
|--------|-------------|
| スキーマ更新にはschema testを必要 | `workflow_spec_v1.json`バリデーション |
| workflow追加にはgoldsetを必要 | `--goldset`引数を強制 |
| tuner導入箇所は回帰テストを必要 | `regression`指標を監視 |
| events.jsonlが欠けたら失格 | ハードゲート尊重 |
