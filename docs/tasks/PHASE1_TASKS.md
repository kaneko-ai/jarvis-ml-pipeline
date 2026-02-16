> Authority: ROADMAP (Level 5, Non-binding)
> Purpose: docs/DEVELOPMENT_PLAN.md の参照先として、Phase 1 のタスク一次資料を提供する

# PHASE 1 TASKS（Week 1-8）

## 目的
Phase 1 は「監査可能性と契約（BUNDLE_CONTRACT）を壊さない」基盤固めを行う。

## Priority A
1. Markdown 整合（リンク切れ 0、正本確立）
2. 契約テスト（固定 10 ファイルの欠損を e2e で検出）
3. 失敗時監査（`fail_reasons` を `audit.json` に出力）
4. 実行入口の一貫性（CLI 経由を優先し、実行経路の乱立を防止）

## Priority B
- Evidence locator の厳格化（空を許容しない）
- seed/version の固定（再現性）
- ログ最小正規化（`run.json` / `audit.json` のキー統一）

## Nice to Have
- ドキュメントの図解（概念図・フロー）
