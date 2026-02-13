> Authority: ROADMAP (Level 5, Non-binding)

# JAVIS Ops+Extract Proof-Driven Plan v2.0

## 目的
- Ops+Extract の成立性を、スタブ検出・契約検証・E2E 検証で継続的に確認しやすい形に整理する。
- 既存の段階実装 C を土台に、No-Stub / Contract / Trace / Resume / Drive Commit を中心に実装を進める。

## 実装範囲
- `scripts/no_stub_gate.py` と CI 連携
- `schemas/ops_extract/*.schema.json` と契約検証
- `trace.jsonl` / `stage_cache.json` / `crash_dump.json`
- `pdf_diagnosis.json` / needs_ocr 改良 / 正規化ハッシュ
- Drive resumable upload 対応 client と commit protocol 強化
- 設定互換・移行スクリプト・セキュリティ補強
- `tests/ops_extract/*` と `tests/e2e/test_ops_extract_proof_driven.py`

## 実装順
1. 計画書とログ運用の開始
2. No-Stub Gate
3. Contract 固定（JSON Schema）
4. DAG Trace と Crash Dump
5. Extract 強化（Diagnosis / OCR 判定 / 正規化証跡）
6. Resume / Determinism
7. Drive 同期（resumable + commit）
8. 互換性・移行・セキュリティ
9. E2E 受け入れゲート

## 受け入れ観点
- `committed_drive=true` を Drive 側確定条件として扱える
- 画像 PDF で OCR 経路が動作し `ingestion/text.md` が出力される
- 中断再実行で重複処理が抑制される
- 失敗学習の記録と preflight での再検知が確認できる
- 最終的に `pytest/ruff/black/mypy/uv build` が緑になる

## ログ運用テンプレート
- 日時
- 段階名
- 実装差分
- 実行コマンド
- 結果（成功/失敗、件数）
- 学習・再発防止
- 次段の着手条件

## 補足
- CI では Drive エミュレータを中心に利用し、実 Drive smoke は環境変数がある場合に実行する。
- `jarvis_core.integrations.additional.GoogleDriveExporter` は既存互換のため維持し、ops_extract 専用 client を別途導入する。
