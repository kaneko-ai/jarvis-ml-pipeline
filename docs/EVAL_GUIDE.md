# Evaluation Guide (v1.2)

> Authority: REFERENCE (Level 2, Non-binding)


> Authority: DEC-006, MASTER_SPEC v1.2

## 概要

JARVISの評価モデルは **Quality Gate（実測）** と **Regression（回帰）** に基づく。
「何となく動く」ではなく、「数値で証明された」状態のみ合格とする。

---

## 1. Quality Gate（一発必中）

すべてのRun（実行）は、生成時に以下のQuality Gateを通過すべきである。
ゲートは `jarvis_core/pipelines/executor.py` および `QualityGateVerifier` によって強制される。

| 指標 | 閾値 | 説明 | 失敗時の挙動 |
|------|------|------|-------------|
| **Provenance Rate** | ≥ 0.95 | 文単位の根拠紐付け率 | `FAIL` (QualityGateFailure) |
| **Facts w/o Evidence** | = 0 | 根拠のない事実提示 | `FAIL` (HallucinationRisk) |
| **Pipeline Completion** | 100% | 全ステージ完走 | `FAIL` (SystemError) |
| **Artifact Contract** | 10 files | 必要成果物の生成 | `FAIL` (ContractViolation) |

### 確認方法

```bash
# 実行後に show-run で確認
python jarvis_cli.py show-run --run-id <RUN_ID>

# Eval結果のみ確認
type logs/runs/<RUN_ID>/eval_summary.json
```

---

## 2. Regression Testing（回帰テスト）

新機能追加やリファクタリング時に、性能劣化がないことを確認するための手順。

### 対象セット

| セット名 | Path | 用途 |
|----------|------|------|
| **Smoke Set** | `evals/smoke_eval_set.json` | 基本動作・契約遵守の確認 (3問) |
| **Offline E2E** | `tests/e2e/fixtures/offline_corpus.json` | ネットワークなしでの動作保証 |
| **CD73 Gold** | `evals/golden_sets/cd73_set_v1.jsonl` | (Phase 2) 順位付け精度の検証 |

### 実行手順

#### A. スモークテスト（Quality Gate確認）

```bash
# 1. 実行
python jarvis_cli.py run --goal "CD73 immunotherapy" --pipeline configs/pipelines/e2e_oa10.yml

# 2. ゲート確認
python jarvis_cli.py show-run
# => "Gate Passed: True" を確認
```

#### B. オフライン回帰

```bash
# ネットワーク遮断状態での保証
python -m pytest tests/e2e/test_e2e_offline.py
```

---

## 3. Phase 2: Intelligence Evaluation

Phase 2（賢さ強化）では、以下の指標が追加される。

- **Citation Precision**: 引用された根拠が本当にその文を支持しているか
- **Ranking NDCG**: 人間（Golden Ranking）との順位一致度
- **Contradiction Detection**: 矛盾する主張を見抜けたか

これらは `jarvis_cli.py eval` コマンド（将来実装）で一括計測する。

## 概要

JARVISの評価システムは**Frozen（回帰）**と**Live（監視）**の2種類で構成される。

## Frozen評価セット

### 場所
- `docs/evals/frozen_immuno_v1.jsonl` (10件)

### 形式
```json
{
  "task_id": "immuno_s1_01",
  "category": "paper_survey",
  "query": "CD73 immunotherapy cancer",
  "expected_entities": ["CD73", "NT5E", "adenosine"],
  "min_citations": 2,
  "notes": "S1: CD73/腫瘍微小環境"
}
```

### しきい値
| 指標 | 初期値 | 目標 |
|------|--------|------|
| claim_precision | ≥ 0.85 | ≥ 0.90 |
| citation_precision | ≥ 0.90 | ≥ 0.95 |
| unsupported_claim_rate | ≤ 0.10 | ≤ 0.05 |

## 回帰テストの実行

```bash
# ローカル実行
python -m jarvis_core.eval.regression_runner \
  --gold docs/evals/frozen_immuno_v1.jsonl \
  --out reports/eval/latest

# CI（GitHub Actions）
# .github/workflows/eval_regression.yml で自動実行
```

## 評価結果の見方

### summary.json
```json
{
  "run_id": "xxx",
  "pass_fail": "pass",
  "metrics": {
    "claim_precision": 0.87,
    "citation_precision": 0.92
  },
  "failing_gates": []
}
```

### 赤になったら

1. **events.jsonl を確認** → どのステップで失敗したか
2. **eval/summary.json を確認** → どの指標が閾値を下回ったか
3. **failing_claims を確認** → どの主張が根拠不足か

## しきい値の更新

1. 品質が安定したらしきい値を締める
2. JARVIS_MASTER.md Section 7.2 を更新
3. PRでレビュー

## Live評価（監視用）

本番環境では各実行で自動的にメトリクスを収集し、
品質劣化を検知したらアラートを出す（将来実装）。
