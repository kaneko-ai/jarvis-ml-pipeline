# Evaluation Guide

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
