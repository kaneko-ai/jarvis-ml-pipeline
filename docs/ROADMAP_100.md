> Authority: ROADMAP (Level 5, Non-binding)

# JARVIS 100-Step Roadmap

現在=1、完了=100。**全100ステップ完了 ✅**

---

## Progress

| Range | Phase | Status | Completion |
|-------|-------|--------|------------|
| 1-20 | 仕様権威固定 + 一本道 | ✅ Complete | 100% |
| 21-40 | Verify強制 | ✅ Complete | 100% |
| 41-60 | 文献パイプライン工具化 | ✅ Complete | 100% |
| 61-80 | Judge/再試行 | ✅ Complete | 100% |
| 81-90 | API/UI契約化 | ✅ Complete | 100% |
| 91-100 | 運用・安全・拡張 | ✅ Complete | 100% |

---

## 1-20: 仕様権威固定 + 一本道 ✅

- [x] 1. docs棚卸し
- [x] 2. SPEC_AUTHORITY.md作成
- [x] 3. DECISIONS.md作成
- [x] 4. Authority Header追記
- [x] 5. spec_lint.py実装
- [x] 6. test_spec_lint.py実装
- [x] 7. CI spec-lint追加
- [x] 8. 例外記録
- [x] 9. CLI一本化（README更新）
- [x] 10. main.py格下げ
- [x] 11. CLI実行例確認
- [x] 12. .env.example追加
- [x] 13. codex_progress.md更新
- [x] 14. run_id生成規約固定
- [x] 15. logs/runs保証
- [x] 16. RunStore唯一化
- [x] 17. Telemetry追随
- [x] 18. run_config.json常時保存
- [x] 19. result.json常時保存
- [x] 20. eval_summary.json常時保存

---

## 21-40: Verify強制 ✅

- [x] 21. Verifyチェック項目定義
- [x] 22. citation要件
- [x] 23. locator要件
- [x] 24. 断定検出
- [x] 25. eval_summary出力
- [x] 26. gate_passed要件
- [x] 27. fail_reasonsコード化
- [x] 28. RUN_ERROR events
- [x] 29. Verify証跡
- [x] 30. Verify未実行ガード
- [x] 31. 根拠フォーマット統一
- [x] 32. 引用整合チェック
- [x] 33. PII検出反映
- [x] 34. Verify失敗メッセージ
- [x] 35. failed完走
- [x] 36. passゴールデンケース
- [x] 37. failゴールデンケース
- [x] 38. 回帰試験固定
- [x] 39. CI回帰
- [x] 40. ゲート外し検知

---

## 41-60: 文献パイプライン工具化 ✅

- [x] 41. paperタスクtyping
- [x] 42. index要件方針
- [x] 43. index無し挙動統一
- [x] 44. build-indexスキーマ
- [x] 45. indexメタ追加
- [x] 46. indexes_used記録
- [x] 47. papers_used記録
- [x] 48. FetchPolicy一致
- [x] 49. 再試行方針
- [x] 50. 外部取得なし制限
- [x] 51. パイプ固定
- [x] 52. 識別子追加
- [x] 53. 引用根拠追加
- [x] 54. extractエラー反映
- [x] 55. evidence薄fail
- [x] 56. 参照文献表示
- [x] 57. reindex手順
- [x] 58. versioning
- [x] 59. CI検査
- [x] 60. ゴールデンケース3本

---

## 61-80: Judge/再試行 ✅

- [x] 61. リトライ戦略定義
- [x] 62. 変更ログ
- [x] 63. 回数上限
- [x] 64. cost/time記録
- [x] 65. 改善eval記録
- [x] 66. 2系統Judge
- [x] 67. 統合判定
- [x] 68. 部分成功定義
- [x] 69. 部分成功非success
- [x] 70. needs_retry返却
- [x] 71. retry policy指定
- [x] 72. リトライ成功ケース
- [x] 73. リトライ停止ケース
- [x] 74. 回帰固定
- [x] 75. 評価指標固定
- [x] 76. 指標出力
- [x] 77. 閾値明示
- [x] 78. 閾値記録
- [x] 79. 閾値未達制限
- [x] 80. PRブロック

---

## 81-90: API/UI契約化 ✅

- [x] 81. /run run_id返却
- [x] 82. /status result.json返却
- [x] 83. UI読むだけ
- [x] 84. fail理由表示
- [x] 85. 参照文献表示
- [x] 86. eval_summary表示
- [x] 87. 契約変更不要確認
- [x] 88. 契約外依存なし
- [x] 89. 回帰保護
- [x] 90. ログ契約検知

---

## 91-100: 運用・安全・拡張 ✅

- [x] 91. PIIテストケース
- [x] 92. 保存ポリシー明文化
- [x] 93. コスト/レイテンシ上限
- [x] 94. 上限超過ステータス
- [x] 95. ログローテーション
- [x] 96. 新機能DoD固定
- [x] 97. Skill登録規約
- [x] 98. Skillテンプレ
- [x] 99. 拡張確認
- [x] 100. Research OS完成

---

## 作成ファイル一覧

| ファイル | Step | 用途 |
|---------|------|------|
| SPEC_AUTHORITY.md | 2 | 権威順位 |
| DECISIONS.md | 3 | 決定記録 |
| spec_lint.py | 5 | 仕様チェック |
| test_spec_lint.py | 6 | lint回帰 |
| spec-lint.yml | 7 | CI |
| README.md | 9 | CLI一本化 |
| run_store_v2.py | 14-20 | Run管理 |
| quality_gate.py | 21-40 | 品質ゲート |
| paper_pipeline.py | 41-60 | 文献パイプ |
| judge.py | 61-80 | Judge/再試行 |
| run_api.py | 81-90 | API契約 |
| security_ops.py | 91-98 | 運用・安全 |
| test_100_steps.py | 99-100 | 検証テスト |
| DoD.md | 100 | 完了定義 |
