> Authority: GATE (Level 3, Binding)

# JARVIS Definition of Done (DoD)

## 100ステップ完了チェックリスト

### Phase 1-20: 仕様権威固定 + 一本道 ✅
- [x] SPEC_AUTHORITY.md作成
- [x] DECISIONS.md作成
- [x] spec_lint.py実装
- [x] Authority Header追加
- [x] README CLI一本化
- [x] RunStore v2作成
- [x] Bundle Contract定義

### Phase 21-40: Verify強制 ✅
- [x] QualityGateVerifier実装
- [x] FailCodes定義
- [x] citation/locator必須
- [x] 断定検出
- [x] PII検出

### Phase 41-60: 文献パイプライン ✅
- [x] PaperPipeline実装
- [x] IndexMeta定義
- [x] sources記録

### Phase 61-80: Judge/再試行 ✅
- [x] Judge 2系統
- [x] RetryManager
- [x] EvalMetrics

### Phase 81-90: API/UI契約 ✅
- [x] RunAPI（run_id返すだけ）
- [x] UIDataProvider（読むだけ）

### Phase 91-100: 運用・安全・拡張 ✅
- [x] PIIDetector
- [x] RetentionPolicy
- [x] AuditLogRotator
- [x] FeatureDoD
- [x] SkillSpec
- [x] test_100_steps.py

---

## 新機能追加要件

新機能をマージするには以下を満たすこと：

1. **テストがある** - tests/配下にtest_*.py
2. **ドキュメントがある** - docs/またはREADME
3. **spec_lintを通過** - 強制語彙ルール遵守
4. **品質ゲートを通過** - citation/locator必須
5. **新警告なし** - WARNING増加禁止
6. **Bundle契約互換** - 成果物規格維持

---

## CI必須チェック

| チェック | 内容 |
|---------|------|
| core_tests | coreテスト通過 |
| spec-lint | Authority違反なし |
| quality-gates | 品質ゲート通過 |

---

## Research OS完成条件

- [ ] 再現性：同一入力で同一出力
- [ ] 監査性：全操作がログに残る
- [ ] 回帰：品質劣化でCI失敗
- [ ] 強制ゲート：citation/locator必須
- [ ] 拡張可能：Skill追加で壊れない
