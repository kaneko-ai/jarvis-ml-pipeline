# OpenAI Codex 自律開発ミッション
# JARVIS Research OS v5.3.0 → v1.0

## 🎯 最終目標
**2026-07-31までにJARVIS Research OS v1.0をリリース（24週間）**

全24件の技術的負債（TD-001〜TD-024）を解消し、100%テストパス・CI成功を達成する。

---

## 📊 現在のステータス（Week 0 - ベースライン）

### バージョン
- **現在**: 5.3.0
- **目標**: 1.0.0
- **リリース日**: 2026-07-31

### テスト状況
- **パス**: 5076 / 6302（スキップ 538）
- **失敗**: 688（Failed 686 / Errors 2）
- **カバレッジ**: 64.11%
- **目標カバレッジ**: ≥ 70%
- **TD-001進捗（test_fix_plan）**: 351 / 689（残り338）

### CI状況
- **ステータス**: ❌ 失敗
- **最終成功**: 不明
- **目標**: ✅ 10回連続成功

---

## 🚀 Phase 2-α: クリティカル修正（Week 1-2）
**ステータス**: 🔄 進行中

### TD-001: 727件のテスト失敗を修正
**優先度**: 🔴 P0 クリティカル
**見積時間**: 80時間
**期限**: Week 2 終了時
**ステータス**: 🔄 開始

---

#### 実行手順

**ステップ0: 初期評価**（15分）
```bash
# プロジェクトディレクトリに移動
cd jarvis-ml-pipeline

# 全テスト実行・結果保存
uv run pytest tests/ -v --tb=line > test_failures.log 2>&1

# 失敗数カウント
grep -E "FAILED|ERROR" test_failures.log | wc -l

# このファイルを実際の数値で更新
実行結果:（ここを更新）

Total Tests: ???
Passing: ???
Failing: ???
Errors: ???
ステップ1: 失敗の分類（30分）

test_failures.log を分析し、test_fix_plan.md を作成：

# テスト修正計画 - TD-001

## 分析日: [日付を入力]
## 総失敗数: [数を入力]

### Category A: インポートエラー（最優先）- P0
**影響**: テストファイル全体がブロック
**件数**: ???

- [ ] tests/test_file1.py - ImportError: No module named 'X'
- [ ] tests/test_file2.py - ImportError: cannot import 'Y'
...

### Category B: アサーションエラー - P1
**影響**: コア機能の不具合
**件数**: ???

- [ ] tests/test_evidence_grading.py::test_grade_rct - AssertionError
- [ ] tests/test_citation.py::test_extract_contexts - Expected 5, got 3
...

### Category C: フィクスチャ不足 - P1
**影響**: テストインフラ
**件数**: ???

- [ ] tests/test_*.py - fixture 'sample_paper' not found
...

### Category D: 非推奨API - P2
**影響**: 外部依存関係の変更
**件数**: ???

- [ ] tests/test_embeddings.py - AttributeError: 'X' has no attribute 'Y'
...

### Category E: タイムアウト/低速テスト - P3
**影響**: CIパフォーマンス
**件数**: ???

- [ ] tests/test_integration.py::test_full_pipeline - Timeout after 60s
...
Copy
ステップ2: 修正ループ実行（各テストに対して繰り返し）

┌─────────────────────────────────────────────┐
│ 1. テストファイルを読む                      │
│    $ cat tests/test_module.py               │
│    理解: 何が期待されているか？              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 2. 実装ファイルを読む                        │
│    $ cat jarvis_core/module/file.py         │
│    理解: 現在の動作は？                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 3. 根本原因を特定                            │
│    - インポート不足？                        │
│    - アサーション誤り？                      │
│    - API変更？                               │
│    - ロジックバグ？                          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 4. コード修正（またはテスト修正）            │
│    最小限の変更で修正                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 5. リントチェック                            │
│    $ uv run ruff check jarvis_core tests    │
│    $ uv run black jarvis_core tests         │
│    テスト前に必ずパスさせる！                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 6. 特定テスト実行                            │
│    $ uv run pytest tests/test_file.py::     │
│      test_name -v                           │
│    期待: PASSED                              │
└─────────────────────────────────────────────┘
                    ↓
          ┌─────────────┐
          │  パス？     │
          └─────────────┘
           /           \
         NO            YES
          │             │
          ↓             ↓
    ┌──────────┐   ┌──────────────────────┐
    │ 分析     │   │ 7. モジュールテスト  │
    │ & 再試行 │   │    $ uv run pytest   │
    │ (最大3回)│   │    tests/test_file.py│
    └──────────┘   └──────────────────────┘
                            ↓
                     ┌─────────────┐
                     │ 全パス？    │
                     └─────────────┘
                      /           \
                    NO            YES
                     │             │
                     ↓             ↓
              ┌─────────────┐   ┌──────────────────┐
              │ リグレッシ  │   │ 8. コミット      │
              │ ョン！      │   │    $ git add .   │
              │ 先に修正    │   │    $ git commit  │
              └─────────────┘   │    -m "fix(...)" │
                                └──────────────────┘
                                        ↓
                                ┌──────────────────┐
                                │ 9. 進捗更新      │
                                │    このファイル  │
                                │    を編集        │
                                └──────────────────┘
                                        ↓
                                ┌──────────────────┐
                                │ 10. 次のテストへ │
                                └──────────────────┘
進捗トラッキング（修正ごとに更新）
セッション1 - [日付]

時間: 00:00 - ??:??
修正テスト数: 0 → ???
コミット数: 0 → ???

修正完了:
- [ ] tests/test_evidence_grading.py::test_1
- [ ] tests/test_evidence_grading.py::test_2
...

ブロッカー:
- なし

次セッション: test_??? から継続
日次サマリーテンプレート

## Day [N] - [日付]

### メトリクス
- 本日の修正数: ???
- 累計修正数: ??? / 727 (??%)
- 作業時間: ?? 時間
- コミット数: ???

### 成果
- ✅ Category A（インポートエラー）完了
- ✅ カバレッジ ??% → ??% に増加

### 課題
- ❌ テストXが継続して失敗 - 詳細分析が必要
- ⚠️ 3件のリグレッション発見 - 即座に修正

### ブロッカー
- 🚫 test_Y は手動レビューが必要 - TODOとしてマーク

### 明日の目標
- Category B の残り50件を修正
- 目標: 累計100件修正
自己検証チェックポイント
10テスト修正ごと: 全テスト実行

Copyuv run pytest tests/ -x --tb=line
最後のテスト（727番目）で停止 → 良好！継続
それ以前で停止 → リグレッション検出！修正してから継続
50テスト修正ごと: カバレッジ確認

Copyuv run pytest --cov=jarvis_core --cov-report=term
カバレッジ%をこのファイルに更新
100テスト修正ごと: CIシミュレーション

Copyuv run ruff check jarvis_core tests
uv run black --check jarvis_core tests
uv run mypy jarvis_core
uv run pytest tests/ -v
全てパスしてから継続
TD-001 成功条件
✅ 全727テストがパス: uv run pytest tests/
✅ リグレッションなし: CI が3回連続成功
✅ カバレッジ: ≥ 70%（--covで測定）
✅ リント: ruff と black がパス
✅ 型チェック: mypy がエラーなし
完了日: [記入予定]

TD-002: 70%テストカバレッジ達成
優先度: 🔴 P0 クリティカル ステータス: ⏳ ブロック中（TD-001完了待ち）

前提条件:

TD-001が100%完了
全既存テストがパス
戦略:

ベースライン測定: uv run pytest --cov=jarvis_core --cov-report=html
htmlcov/index.html を開く → 70%未満のモジュールを特定
優先順位:
P0: jarvis_core/evidence/（Phase 2要件で≥85%必須）
P0: jarvis_core/citation/（≥80%必須）
P0: jarvis_core/contradiction/（≥75%必須）
P1: その他のコアモジュール
カバーされていないコードパスごとに:
tests/test_module.py にテスト追加
テスト実行 → パス
カバレッジ増加を確認
コミット
開始日: [TD-001完了後]

TD-003: Bundle契約の統一
優先度: 🔴 P0 クリティカル ステータス: ⏳ キュー

確認すべきファイル:

docs/contracts/BUNDLE_CONTRACT.md - 必須10ファイルを確認
scripts/ci_run.py - 全10ファイル生成を検証
jarvis_core/storage/ - ストレージロジック確認
実装:

scripts/validate_bundle.py に検証関数追加
CIから呼び出し: .github/workflows/ci.yml
モック実行でテスト
TD-004: Quality Gate実装
優先度: 🔴 P0 クリティカル ステータス: ⏳ キュー

実装:

scripts/quality_gate.py を作成:
check_gate_passed() → bool
ルール: gate_passed == false → status = "failed"
scripts/ci_run.py に統合
.github/workflows/ci.yml にCIチェック追加
🔄 Phase 2-β: 品質と安定性（Week 5-10）
ステータス: ⏳ 計画中

[TD-005〜TD-010の詳細 - Phase 2-α完了後に展開]

🌐 Phase 3-α: エコシステム（Week 11-16）
ステータス: ⏳ 計画中

[TD-011〜TD-017の詳細]

🎨 Phase 3-β: 仕上げとリリース（Week 17-24）
ステータス: ⏳ 計画中

[TD-018〜TD-024の詳細]

📈 週次進捗レポートテンプレート
Copy# Week [N] レポート

## 完了
- ✅ TD-XXX: [説明]

## 進行中
- 🔄 TD-XXX: [説明] - [完了率%]

## ブロック
- 🚫 TD-XXX: [説明] - [ブロック理由]

## メトリクス
- テスト: ??? / 727 パス
- カバレッジ: ??%
- CIステータス: ???
- コミット数: ???

## 来週の計画
- [ ] TD-XXX 完了
- [ ] TD-XXX 開始
🚨 緊急プロトコル
同じ問題で2時間以上スタックした場合
blockers.md にドキュメント化
次のテスト/タスクに移動
コンテキストを得てから戻る
CIが継続して失敗する場合
.github/workflows/ci.yml の変更必要箇所を確認
ローカルでCIを実行: act（GitHub Actionsシミュレーター）
必要ならCI設定を修正
時間が足りない場合
P0 > P1 > P2 > P3 の優先順位を厳守
期限を守るためにP3をスキップ可
スキップした項目はv1.1用にドキュメント化
🎓 参考資料
プロジェクトドキュメント: docs/
アーキテクチャ: docs/JARVIS_ARCHITECTURE.md
ロードマップ: docs/ROADMAP.md
テストガイド: tests/README.md（存在する場合）
最終更新: [日付] 更新者: OpenAI Codex Agent 次回レビュー: TD-001完了後
