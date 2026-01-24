# JARVIS 開発ツールガイド

> Authority: GUIDE (Level 3, Non-binding)

## 開発環境セットアップ

### 1. Python環境
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -e ".[dev]"
```

### 2. pre-commit
```bash
pip install pre-commit
pre-commit install
```

初回実行：
```bash
pre-commit run --all-files
```

---

## コードスタイル

### フォーマッター: Ruff
```bash
ruff format .
```

### リンター: Ruff
```bash
ruff check . --fix
```

---

## テスト

### 実行
```bash
pytest tests/ -v
```

### カバレッジ
```bash
pytest tests/ --cov=jarvis_core --cov-report=html
```

---

## AIコーディング時のルール

### 必須ルール
1. **1PR = 1目的**：複数の目的を混ぜない
2. **Interface-first**：実装前にインターフェースを定義
3. **Budget無視禁止**：新しいツール呼び出しは必ずBudget経由
4. **テスト無しの変更禁止**：テストを追加しないPRは却下

### Budget統合
新しいツール呼び出しを追加する場合：
```python
from jarvis_core.budget import BudgetSpec, BudgetTracker, BudgetPolicy

# 1. Trackerに記録
tracker.record_tool_call()

# 2. 予算チェック
policy = BudgetPolicy()
decision = policy.decide(spec, tracker)

if not decision.should_search:
    tracker.record_degrade(decision.degrade_reason)
    # degraded処理...
```

### Ranking統合
新しいランキング対象を追加する場合：
```python
from jarvis_core.ranking import RankingItem, HeuristicRanker, log_ranking

# RankingItemに変換
items = [RankingItem(id, "type", features={...}) for ...]

# ランキング
ranker = HeuristicRanker()
ranked = ranker.rank(items, context={})

# ログ
log_ranking("logs/ranking.jsonl", task_id, "stage", items, [i.item_id for i in ranked])
```

---

## 将来の拡張ポイント

### 1. LightGBMランキング
- `jarvis_core/ranking/lgbm_ranker.py` を追加
- `config.yaml` の `ranking.backend: lgbm` で切替

### 2. 画像バックエンド
- `jarvis_tools/image_backends/` を作成予定
- 画像生成は backend 抽象で扱う方針

### 3. 分子探索
- `jarvis_core/domains/molecule/` を将来追加
