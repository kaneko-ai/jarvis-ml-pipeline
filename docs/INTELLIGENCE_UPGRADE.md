# JARVIS Intelligence Upgrade Guide

## 概要

Javis 完成度 4.5 → 10 への強化計画。

---

## Phase 1: 判断材料化（5→6）

### 5軸評価
| 軸 | 問い | 5点 | 1点 |
|----|------|-----|-----|
| Relevance | Javisを強化するか | 中核機能直接強化 | 本質からズレ |
| Novelty | 差分は何か | 概念レベルで新しい | 実装済み |
| Evidence | 根拠は何か | 査読論文+コード | SNS/主観 |
| Effort | 導入コスト | 1日以内 | 大規模改修 |
| Risk | 失敗時の影響 | ロールバック容易 | OS破壊 |

### 判断ルール
```python
if relevance >= 4 and evidence >= 3 and effort >= 3 and risk >= 3:
    decision = ACCEPT
else:
    decision = REJECT
```

### Reject理由（6種）
- evidence_insufficient
- relevance_low
- effort_too_high
- risk_too_high
- already_covered
- premature

---

## Phase 2: 再利用知能（6→7.5）

### DecisionItem
Issue はイベント、Decision は知識。

### 類似判断検索
新Issue生成時に過去のDecision Top3を必ず提示。

### 判断パターン
- early-stage-reject（流行初期・根拠不足）
- high-effort-delay（コスト高→後回し）
- evaluator-first（まず評価系強化）

---

## Phase 3: 自己評価（7.5→9）

### Outcome評価
採用後n週で評価: success / neutral / failure

### 成績表
```json
{
  "accept_success_rate": 0.72,
  "reject_correct_rate": 0.81,
  "regret_rate": 0.08
}
```

---

## Phase 4: 研究パートナー（9→10）

### 問い生成
- 未検証点は何か
- 既存手法の前提は何か
- 次に検証すべき仮説は何か

### Action Plan
```
READ: 論文A（理由）
BUILD: 検証コードB（理由）
IGNORE: 論文C（理由）
```

---

## 使用方法

```python
from jarvis_core.intelligence import (
    IntelligentEvaluator,
    DecisionMaker,
    QuestionGenerator,
    ActionPlanner,
)

# 5軸評価
evaluator = IntelligentEvaluator()
scores = evaluator.evaluate("新機能提案", "詳細説明")

# 判断
maker = DecisionMaker()
decision = maker.decide("id1", "提案", scores)

# 問い生成
qgen = QuestionGenerator()
questions = qgen.generate("免疫療法")

# 行動計画
planner = ActionPlanner()
plan = planner.quick_plan(
    topic="免疫療法",
    top_papers=["Paper A"],
    implementation_ideas=["検証コード"],
    low_priority=["古い論文"],
)
```
