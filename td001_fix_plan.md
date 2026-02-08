# TD-001 修正計画（実績）

## 作成日
2026-02-08

## 対象
- 初回再現: 66件（65 failed + 1 error）
- 完了後: 0件（0 failed + 0 errors）
- 検証コマンド: `uv run pytest tests/ -x --ignore=tests/e2e --ignore=tests/integration -q`

## カテゴリ別対応

### Cat-A: テスト順序依存 / 状態汚染（8件）
- [x] quality gate 空回答系の順序依存を解消
- [x] claim_set / execution retry の状態依存を解消
- [x] lab automation の時刻・状態依存を解消
- [x] embedding fallback の順位不安定を解消

### Cat-B: インポートエラー / 公開API欠落（16件）
- [x] `jarvis_core.cache.backend` / `jarvis_core.cache.policy` 追加
- [x] `jarvis_core.evaluation.evaluator` / `jarvis_core.evaluation.metrics` 追加
- [x] `jarvis_core.api.arxiv` に互換 import/メソッド追加
- [x] `tests/conftest.py` に `module` fixture を追加
- [x] report builder の patch 面（docx/pptx）を復旧

### Cat-C: アサーション不一致 / 互換契約差分（33件）
- [x] `jarvis_core/lab/automation.py` に旧API互換 shim を追加
- [x] `jarvis_core/artifacts/claim_set.py` の旧シグネチャ互換を追加
- [x] `jarvis_core/plugins/zotero_integration.py` の旧引数互換を追加
- [x] `jarvis_core/sources/unpaywall_client.py` に `email` 互換プロパティを追加
- [x] `jarvis_web/contracts/api_map_v1.json` の required base_paths を補完

### Cat-D: エンコード / OS依存（6件）
- [x] `jarvis_core/style/language_lint.py` のエンコードフォールバックを追加
- [x] `jarvis_core/security/terminal.py` の Windows `pwd` 互換を追加
- [x] `jarvis_core/ingestion/robust_extractor.py` の fitz fallback を強化

### Cat-E: 品質検知ロジック（1件）
- [x] `scripts/detect_garbage_code.py` の `return None` 検知を Python 3.10+ AST 互換化

### Cat-F: 設計変更が必要（0件）
- [x] 該当なし（スキップ付与なし）

## 実行順序（実績）
1. Cat-B（import/API面）
2. Cat-C（互換契約）
3. Cat-D（環境依存）
4. Cat-A（順序依存）
5. Cat-E（品質検知）
6. Cat-F（該当なし）

## 完了判定
- [x] `pytest`（ignore e2e/integration）で 0 failed, 0 errors
- [x] `ruff` PASS
- [x] `black --check` PASS
- [x] 回帰なしを確認
