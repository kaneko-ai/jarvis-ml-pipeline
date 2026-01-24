# Live Evaluation Guide

> Authority: REFERENCE (Level 2, Non-binding)


## 概要

Live評価は「運用中の品質劣化」を検知するための定点観測。

## 実行方法

```bash
# 手動実行
python -c "from jarvis_core.eval.live_runner import run_live_eval, DEFAULT_LIVE_QUERIES; run_live_eval(DEFAULT_LIVE_QUERIES)"

# シェルスクリプト (cron用)
bash scripts/live_monitor.sh
```

## 出力

```
reports/live/
├── 2024-12-21/
│   ├── results.jsonl
│   └── summary.json
├── 2024-12-22/
│   └── ...
```

## アラート条件

| 指標 | 正常範囲 | アラート条件 |
|------|----------|--------------|
| retrieval_success_rate | ≥ 0.7 | 3日連続で < 0.5 |
| avg_latency_ms | ≤ 5000 | 3日連続で > 10000 |

## 手動対応手順

### 取得成功率低下時
1. PMC OA API の状態確認
2. Unpaywall API の状態確認
3. Index 再構築を検討

### レイテンシ上昇時
1. Index サイズ確認
2. キャッシュ hit rate 確認
3. LLM provider の応答速度確認

## 関連ドキュメント
- [EVAL_GUIDE.md](./EVAL_GUIDE.md) - Frozen評価
- [TECH_DEBT.md](./TECH_DEBT.md) - 既知の問題
