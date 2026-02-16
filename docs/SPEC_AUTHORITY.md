> Authority: SPEC (Level 2, Binding)
> Canonical: YES
> Purpose: 仕様・計画・実装・ログの「衝突」を解決するための最上位ルール

# SPEC AUTHORITY（仕様権威階層）

## 1. 目的
JARVIS Research OS の文書群・設定・コード・ログに矛盾が発生した場合、
「どれを正とするか」を機械的に決め、誤解・暴走・恣意的解釈を禁止する。

## 2. 優先順位（高いほど強い）
以下の順で優先する。上位が下位に勝つ。

### Level 0: Human Authority（人間の最終権威）
- 金子優（Owner）が明示した決定・制約・禁止事項
- 例：採用/不採用、公開範囲、規約順守、予算、時間制約

### Level 1: MASTER SPEC（最上位仕様）
- docs/MASTER_SPEC.md
- 「非交渉原則」「成功の定義」「品質ゲート」「成果物契約」等の核

### Level 2: SPEC（機能仕様）
- 本ファイルおよび docs/ 以下の SPEC（例：FEATURE SPEC）
- 1機能単位の要件・入力・出力・DoD

### Level 3: CONTRACT（契約・スキーマ）
- docs/BUNDLE_CONTRACT.md
- policies/API_CONTRACT.md
- YAML/JSON schema、フォルダ構造契約、成果物契約

### Level 4: RUNBOOK / PLAYBOOK（運用手順）
- docs/RUNBOOK_*.md / docs/*PLAYBOOK*.md など
- 実行手順・障害対応・リリース手順

### Level 5: ROADMAP / PLAN（計画書）
- docs/DEVELOPMENT_PLAN.md 等
- 目標や優先度の参考。拘束力は弱い（Non-binding）

### Level 6: README / NOTES（説明）
- README.md、メモ類
- 参考情報。仕様の代替にはならない。

## 3. 衝突時の解決ルール（絶対ルール）
- 仕様とコードが衝突：仕様が正。コードを修正する。
- 仕様とログが衝突：ログが事実。仕様を修正するか「失敗」とする。
- Plan と Spec が衝突：Spec が正。Plan を更新する。
- “存在しない参照先”は即エラー：参照元を修正し、リンク切れをゼロにする。

## 4. 変更管理（Decisions）
- 仕様変更・重要判断は docs/DECISIONS.md に記録する。
- 仕様の重大変更は「なぜ」「何が変わる」「後方互換」「リスク」を必ず書く。

## 5. 禁止事項
- 根拠なしの断言（仕様の書き換えによる辻褄合わせ）
- “とりあえず動く” を理由に契約を曖昧化すること
- Human Authority を迂回する自動化（承認の空文化）
