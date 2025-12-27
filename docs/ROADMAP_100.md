> Authority: ROADMAP (Level 5, Non-binding)

# JARVIS 100-Step Roadmap

現在=1、完了=100。再現性・監査性・回帰・強制ゲートが揃った Research OS としての完成を目指す。

---

## Progress

| Range | Phase | Status | Completion |
|-------|-------|--------|------------|
| 1-20 | 仕様権威固定 + 一本道 | 🟡 In Progress | 60% |
| 21-40 | Verify強制 | ⬜ Not Started | 0% |
| 41-60 | 文献パイプライン工具化 | ⬜ Not Started | 0% |
| 61-80 | Judge/再試行 | ⬜ Not Started | 0% |
| 81-90 | API/UI契約化 | ⬜ Not Started | 0% |
| 91-100 | 運用・安全・拡張 | ⬜ Not Started | 0% |

---

## 1-20: 仕様権威固定 + 一本道

- [x] 1. docs棚卸し：仕様っぽい文書一覧化
- [x] 2. SPEC_AUTHORITY.md作成（権威順位・裁定ルール確定）
- [x] 3. DECISIONS.md作成（決定記録を開始）
- [ ] 4. 主要docsにAuthority Header追記（分類を固定）
- [x] 5. spec_lint.py実装（REFERENCE/ROADMAPで強制語彙禁止）
- [x] 6. test_spec_lint.py実装（回帰固定）
- [ ] 7. CIにspec_lint追加し、違反で落ちることを確認
- [ ] 8. Authority例外が必要ならDECISIONSに記録
- [ ] 9. 入口をCLIに一本化（README/guide更新）
- [ ] 10. main.pyをデモ扱いに格下げ（入口から排除）
- [ ] 11. CLI実行例がargparseと一致していることを確認
- [ ] 12. .env.exampleをQuickstartに必須化
- [ ] 13. codex_progress.mdのStatusを現状で埋める
- [ ] 14. run_id生成規約を固定
- [ ] 15. logs/runs/{run_id}が常に作成されることを保証
- [ ] 16. RunStoreをパスの唯一決定者にする
- [ ] 17. Telemetry loggerをRunStoreに追随させる
- [ ] 18. run_config.jsonを常に保存
- [ ] 19. 失敗時でもresult.jsonを常に保存
- [ ] 20. 失敗時でもeval_summary.jsonを常に保存

---

## 21-40: Verify強制（価値の中核）

- [ ] 21. Verifyのチェック項目（最低限）を定義
- [ ] 22. citationゼロの成功を禁止（例外条件だけ明文化）
- [ ] 23. citationに根拠位置情報が無い成功を禁止
- [ ] 24. "断定の危険"の検出ルールを実装
- [ ] 25. Verify結果をeval_summary.jsonに出す
- [ ] 26. gate_passedをsuccessの必要条件にする
- [ ] 27. fail_reasonsを定型コード化
- [ ] 28. RUN_ERROR等のイベントがevents.jsonlに残る
- [ ] 29. Verifyが実行された証跡をeventsに残す
- [ ] 30. Verify未実行でsuccessにならないガードを追加
- [ ] 31. "根拠提示"のフォーマットを統一
- [ ] 32. 引用整合の最低チェック
- [ ] 33. PII/インジェクション検出結果をfail理由に反映
- [ ] 34. Verify失敗時の標準メッセージを整備
- [ ] 35. Verify失敗でもrun全体は"failed"で完走
- [ ] 36. 代表タスクでVerify passのゴールデンケースを作る
- [ ] 37. 代表タスクでVerify failのゴールデンケースを作る
- [ ] 38. その2ケースをtests/に回帰試験として固定
- [ ] 39. CIで回帰が常に走るようにする
- [ ] 40. "品質ゲートを外す変更"が入るとCIで落ちる

---

## 41-60: 文献パイプライン工具化（再現性の核）

- [ ] 41. paperタスクのcategory/typingを固定
- [ ] 42. paperタスクはindexを必須にする方針を確定
- [ ] 43. indexが無い場合の挙動を統一
- [ ] 44. build-indexの成果物スキーマをdocsに固定
- [ ] 45. indexのメタ情報を必須化
- [ ] 46. run結果にindexes_usedを残す
- [ ] 47. run結果にpapers_usedを残す
- [ ] 48. paper取得のFetchPolicyをdocsと一致させる
- [ ] 49. 取得失敗時の再試行方針を決める
- [ ] 50. "外部取得なし要約"を禁止する（paperでは）
- [ ] 51. chunk→根拠→要約のパイプを固定
- [ ] 52. 参照文献の識別子（DOI/PMID/URL）を必須化
- [ ] 53. "引用根拠（段落/文）"の最低情報を必須化
- [ ] 54. evidence抽出のエラーをfail理由へ反映
- [ ] 55. evidenceが薄い場合はfailかneeds_retryに落とす
- [ ] 56. show-runに"参照文献一覧"表示を追加
- [ ] 57. 索引の再生成（reindex）の手順をdocsに固定
- [ ] 58. indexの互換性破壊をversioning
- [ ] 59. indexスキーマの検査をCIに入れる
- [ ] 60. paperサーベイのゴールデンケースを3本に増やす

---

## 61-80: Judge/再試行（自動で品質を上げる）

- [ ] 61. fail理由ごとにリトライ戦略を定義
- [ ] 62. リトライ前後で"何を変えたか"をログに残す
- [ ] 63. リトライ回数上限を設ける
- [ ] 64. リトライごとにcost/timeを記録
- [ ] 65. リトライで改善したかをevalに記録
- [ ] 66. judgeを2系統（形式/引用整合）にする
- [ ] 67. 2系統の結果を統合した判定規約を固定
- [ ] 68. "部分成功"の扱いを定義
- [ ] 69. 部分成功はsuccess扱いにしない
- [ ] 70. 部分成功は"needs_retry/failed"として次行動を返す
- [ ] 71. CLIに"retry policy"を指定可能にする
- [ ] 72. 代表タスクで自動リトライが通るケースを作る
- [ ] 73. 代表タスクで自動リトライが止まるケースを作る
- [ ] 74. それらを回帰試験に固定
- [ ] 75. 評価指標（citation_count, evidence_coverage等）を固定
- [ ] 76. その指標をeval_summary.jsonに出す
- [ ] 77. 指標の閾値をdocsで明示
- [ ] 78. 閾値変更はDecisionLogで記録必須
- [ ] 79. CIで閾値未達がsuccessになることを禁止
- [ ] 80. "品質が落ちるPR"を確実にブロックできる状態

---

## 81-90: API/UIはログ契約にぶら下げる

- [ ] 81. /run APIは"run_idを返すだけ"に寄せる
- [ ] 82. /status/{run_id}はresult.jsonを返すだけに寄せる
- [ ] 83. UIはlogs/runsを読むだけ（UIが判定しない）
- [ ] 84. UIに"fail理由"を表示
- [ ] 85. UIに"参照文献"を表示
- [ ] 86. UIに"eval_summary（指標）"を表示
- [ ] 87. UI追加で契約変更が必要にならないことを確認
- [ ] 88. UIは契約外ファイルに依存しない
- [ ] 89. UI更新は回帰試験の結果で守られている
- [ ] 90. "ログ契約が壊れるとUIも落ちる"ことがCIで検知できる

---

## 91-100: 運用・安全・拡張

- [ ] 91. PII/インジェクションのテストケースを増やす
- [ ] 92. 保存ポリシー（保持期間・マスキング）を明文化
- [ ] 93. 推論コスト上限とレイテンシ上限を設定
- [ ] 94. 上限超過時のステータスを定義
- [ ] 95. 監査ログのローテーション/肥大化対策を入れる
- [ ] 96. 新機能追加のDoD（契約・ゲート・回帰）をdocsに固定
- [ ] 97. Plugin/Skill登録規約を固定
- [ ] 98. 新skillのテンプレを用意
- [ ] 99. "最小の強い核"が壊れずに拡張できることを確認
- [ ] 100. Research OSとして完成状態
