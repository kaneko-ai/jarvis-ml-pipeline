# Definition of Done (DoD)

PRは以下を**すべて**満たさない限り完了扱いにしない。

---

## 必須条件

### 1. 目的の明確化
- [ ] **Why** が1文で書ける
- [ ] Issue/PR説明に Goal / Non-Goal が明記されている

### 2. 受け入れ基準
- [ ] **AC（Acceptance Criteria）** がテスト可能な形式で記載されている
- [ ] AC達成を確認するテストが追加/更新されている

### 3. Budget制御
- [ ] Budget制御を**無視する例外ルート**が無い
- [ ] 新しいツール呼び出しは `BudgetTracker` 経由で記録される
- [ ] 予算超過時の挙動が明確（degradeまたは停止）

### 4. 観測性（Observability）
- [ ] ログに「**判断理由**」「**省略理由**」「**コスト消費**」が残る
- [ ] degrade時は理由がユーザー向け出力にも含まれる

### 5. ドキュメント
- [ ] 追加/変更したインターフェースが `docs/` に反映
- [ ] 破壊的変更がある場合は **Migration Guide** を追加

### 6. テスト
- [ ] `tests/` にテストが追加/更新されている
- [ ] `pytest` が通る
- [ ] 既存の統合テストが壊れていない

### 7. 品質
- [ ] "人格" の変更は**出力整形層のみ**（推論層に混ぜない）
- [ ] 80文字/行を大幅に超えないこと（可読性）

---

## PRチェックリスト

PRテンプレートに含めるべき項目：

```markdown
## Goal
[このPRが達成すること]

## Non-Goal
[このPRでは扱わないこと]

## Acceptance Criteria
- [ ] [テスト可能なAC1]
- [ ] [テスト可能なAC2]

## Budget Impact
- Tool calls: [追加/削減]
- Retries: [影響]
- Search depth: [影響]

## Observability
- [x] ログ追加/変更点

## Rollback Plan
[戻し方]
```

---

## 回帰基準

以下が壊れた場合、PRは却下：

1. 既存の統合テスト
2. Budget/Rankerの最小テスト
3. Golden Testがあればそのpass率
