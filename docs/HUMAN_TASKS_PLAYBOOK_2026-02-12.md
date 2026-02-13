> Authority: ROADMAP (Level 5, Non-binding)

# Human Tasks Playbook (2026-02-13)

## 目的
- Ops+Extract の実装状況を 2026-02-13 時点で整理する。
- docs 配下の md を 5 ファイル構成で維持する。

## 進捗サマリー
- ランディングページ刷新、SEO、OGP/Favicon 整備は別ブランチで進行済み。
- Ops+Extract は段階実装A/Bに続き、段階実装Cまで反映済み。

## 段階実装A（反映済み）
- needs_ocr 判定
- YomiToku CLI 経路
- `manifest.json` / `metrics.json` / `failure_analysis.json` 出力
- `run_task` の `ops_extract` 経路分岐（LLM初期化スキップ）

## 段階実装B（反映済み）
- preflight チェック（入力存在、ディスク空き、Drive認証、lessons ルール反映）
- failure learning（`knowledge/failures/lessons_learned.md` 追記 + ロック制御）
- Drive 同期雛形（`sync_state.json`）
- retention（`_trash_candidates` への移動と期限削除）

## 段階実装C（今回反映）

### C1: Drive同期の commit 方式
- `manifest.json` を Drive 同期の最終ステップとして扱う構成へ更新。
- 同期時に draft (`committed=false`) と final (`committed=true`) を分けて処理。
- `metrics.ops.manifest_committed_drive` と `manifest.ops.sync_state` を同期結果で更新。

### C2: retry / resume 強化
- `sync_state.json` を拡張。
  - `version`, `state`, `uploaded_files`, `pending_files`, `failed_files`, `retries`, `resume_count`, `last_error`, `manifest_committed_drive`, `last_attempt_at`, `committed_at`
- 既存 `sync_state.json` を読み込んで再開し、`path + size + sha256` 一致ファイルは再送対象から除外。
- `failed_files` がある場合は失敗対象を優先して再送。
- 指数バックオフ付き再試行（`retry_backoff_sec * 2^n`）を反映。

### C3: parse / ocr / upload 並列化
- parse を `parse_workers` で並列化。
- OCR を `ocr_workers` で並列化。
- upload は `upload_workers` を維持して Drive 側で並列処理。
- 入力順保持のため `doc_index` で最終整列。
- ワーカースレッド内で `RobustPDFExtractor` / `TextNormalizer` を都度生成。

### C4: lessons / preflight ルール粒度調整
- lessons の `block_rule` を `hard:<rule>` / `warn:<rule>` 形式で解釈可能に拡張。
- 既存形式（prefixなし）は `hard` として扱う。
- `preflight.rule_mode=warn` で hard 失敗を warning 側へ降格。
- OCR要件判定後に `check_yomitoku_available` を再評価する二段チェックを追加。
- preflight 詳細（checks/errors/warnings）を `run_metadata.json.preflight` に保存。

### C5: retention 調整
- `max_delete_per_run` を追加。
- `dry_run` 時は移動/削除を行わず、差分のみ返す。
- `pinned=true` run を保持対象として扱う。

## 設定キー（run_config.extra.ops_extract）
- 既存キー
  - `enabled`, `parse_workers`, `ocr_workers`, `upload_workers`
  - `thresholds.min_total_chars`, `thresholds.min_chars_per_page`, `thresholds.empty_page_ratio_threshold`
  - `yomitoku.mode`, `yomitoku.figure`
  - `sync.enabled`, `sync.dry_run`
  - `drive.access_token`, `drive.folder_id`
  - `lessons_path`, `stop_on_preflight_failure`, `min_disk_free_gb`
- 段階実装Cで追加
  - `sync.max_retries`, `sync.retry_backoff_sec`, `sync.verify_sha256`
  - `preflight.rule_mode` (`strict` or `warn`)
  - `retention.failed_days`, `retention.success_days`, `retention.trash_days`, `retention.max_delete_per_run`, `retention.dry_run`

## 成果物（ops_extract）

### 既存契約
- 既存 10 ファイル契約は維持。
- `warnings.jsonl` は継続利用。

### 追加成果物
- `manifest.json`
- `run_metadata.json`
- `metrics.json`
- `warnings.json`
- `failure_analysis.json`
- `sync_state.json`
- `ingestion/text.md`
- `ingestion/text_source.json`
- `ocr/ocr_meta.json`（OCR 経路時）

## テスト結果（2026-02-13）
- `uv run pytest -q tests/ops_extract tests/test_run_task_ops_extract_mode.py tests/sync/test_queue.py tests/sync/test_auto_sync.py tests/test_validate_bundle.py`
  - 47 passed
- `uv run pytest -q`
  - 6426 passed, 468 skipped, 1 skipped(collection)

## 静的チェック・ビルド（2026-02-13）
- `uv run ruff check jarvis_core tests` pass
- `uv run black --check jarvis_core tests` pass
- `uv run mypy --explicit-package-bases --follow-imports=skip jarvis_core/evidence/ jarvis_core/contradiction/ jarvis_core/citation/ jarvis_core/sources/ --ignore-missing-imports` pass
- `python tools/spec_lint.py` pass
- `uv build` pass

## 次段候補
- Drive 側 file_id 管理を強化して差分同期を細分化する。
- preflight と lessons の運用ルールを実運用データで調整する。
- retention の運用値を run 数に合わせて再調整する。

## 補足
- ファイル名 `docs/HUMAN_TASKS_PLAYBOOK_2026-02-12.md` は既存スクリプト参照のため継続。

## Proof-Driven v2.0 実装ログ

### ログ運用テンプレート
- 日時
- 段階名
- 実装差分
- 実行コマンド
- 結果（成功/失敗、件数）
- 学習・再発防止
- 次段の着手条件

### 2026-02-13 / Stage 1: 計画書とログ運用開始
- 日時
  - 2026-02-13
- 段階名
  - Stage 1: 計画書MD作成とログ運用開始
- 実装差分
  - `docs/PLANS/JAVIS_OPS_EXTRACT_PROOF_DRIVEN_PLAN_V2.md` を追加
  - 本ファイルに `Proof-Driven v2.0 実装ログ` セクションを追加
- 実行コマンド
  - `uv run pytest -q tests/ops_extract tests/test_run_task_ops_extract_mode.py tests/sync/test_queue.py tests/sync/test_auto_sync.py tests/test_validate_bundle.py`
  - `uv run pytest -q`
  - `uv run ruff check jarvis_core tests`
  - `uv run black --check jarvis_core tests`
  - `uv run mypy --explicit-package-bases --follow-imports=skip jarvis_core/evidence/ jarvis_core/contradiction/ jarvis_core/citation/ jarvis_core/sources/ --ignore-missing-imports`
  - `uv build`
- 結果（成功/失敗、件数）
  - 成功: `47 passed`（ops_extract 関連）
  - 成功: `6426 passed, 468 skipped`（全体）
  - 成功: ruff / black / mypy / build
- 学習・再発防止
  - 既存実装は段階Cまで安定しており、以後は証明系ゲート追加を中心に進めると差分管理しやすい
- 次段の着手条件
  - No-Stub Gate の実装と CI 連携、単体テスト追加

### 2026-02-13 / Stage 2: No-Stub Gate
- 日時
  - 2026-02-13
- 段階名
  - Stage 2: No-Stub quality gate の導入
- 実装差分
  - `scripts/no_stub_gate.py` を追加（TODO/FIXME、pass-only、return定数、dummy id、`ok:true` を検知）
  - `configs/no_stub_allowlist.txt` を追加（`path_glob|code|line|reason` 形式）
  - `.pre-commit-config.yaml` に `no-stub-gate` ローカルフックを追加
  - `.github/workflows/ci.yml` の lint job に no-stub 実行ステップを追加
  - `tests/quality/test_no_stub_gate.py` を追加
- 実行コマンド
  - `uv run pytest -q tests/quality/test_no_stub_gate.py`
  - `uv run python scripts/no_stub_gate.py --paths jarvis_core/ops_extract`
- 結果（成功/失敗、件数）
  - 成功: `5 passed`
  - 成功: `NO_STUB_GATE: PASS`
- 学習・再発防止
  - リポジトリ全体には既存 TODO が多いため、最初は `jarvis_core/ops_extract` 範囲で運用を開始すると段階導入しやすい
- 次段の着手条件
  - ops_extract 契約用 JSON Schema と validator 実装、契約テスト追加

### 2026-02-13 / Stage 3: Contract固定（JSON Schema + Contract Test）
- 日時
  - 2026-02-13
- 段階名
  - Stage 3: 契約スキーマ固定と検証導線の実装
- 実装差分
  - `schemas/ops_extract/` を追加し、`manifest/metrics/warnings/failure_analysis/run_metadata/sync_state/trace/stage_cache` の8スキーマを追加
  - `jarvis_core/ops_extract/schema_validate.py` を追加し、JSON Schemaベースの検証APIを実装
  - `scripts/validate_ops_extract_contracts.py` を追加し、run directory単位で契約検証できるCLIを追加
  - `jarvis_core/ops_extract/orchestrator.py` / `jarvis_core/ops_extract/drive_sync.py` / `jarvis_core/ops_extract/manifest.py` / `jarvis_core/ops_extract/metrics.py` / `jarvis_core/ops_extract/failure_analysis.py` に `schema_version` と互換キーを反映
  - `tests/ops_extract/test_contract_schemas.py` を追加
  - `pyproject.toml` に `jsonschema` 依存を追加し `uv.lock` を更新
- 実行コマンド
  - `uv lock`
  - `uv run pytest -q tests/ops_extract/test_contract_schemas.py tests/ops_extract/test_metrics_manifest.py tests/ops_extract/test_ops_extract_orchestrator.py tests/ops_extract/test_sync_resume_commit.py`
- 結果（成功/失敗、件数）
  - 成功: `14 passed`
  - 成功: contract schema validator と既存ops_extract主要テストが共存
- 学習・再発防止
  - スキーマ導入時は既存互換キー（`version` / `committed`）を残しつつ `schema_version` を追加すると破壊的変更を避けられる
  - JSONL（`trace.jsonl`）は単一オブジェクトschemaを行単位で検証する実装が運用しやすい
- 次段の着手条件
  - DAG固定stage ID、`trace.jsonl` 実出力、失敗時 `crash_dump.json` を追加して成功・失敗双方で契約検証できること

### 2026-02-13 / Stage 4: DAG固定 + Trace + Crash Dump
- 日時
  - 2026-02-13
- 段階名
  - Stage 4: stage ID固定、`trace.jsonl`、`crash_dump.json` 導入
- 実装差分
  - `jarvis_core/ops_extract/orchestrator.py` に固定stage ID（`preflight` 〜 `retention_mark`）を実装
  - 各stageの `start_ts/end_ts/duration/inputs(outputs+sha256)/retry_count/error` を `trace.jsonl` に記録
  - stage未実行時も `error=skipped` で埋めて、1run=1trace の整形を保証
  - 失敗時に `crash_dump.json`（OS/Python/deps/GPU/disk/locale）を出力
  - `contracts.py` で `trace.jsonl` を optional artifact に追加
  - `tests/ops_extract/test_trace_contract.py`, `tests/ops_extract/test_crash_dump.py` を追加
- 実行コマンド
  - `uv run pytest -q tests/ops_extract/test_trace_contract.py tests/ops_extract/test_crash_dump.py tests/ops_extract/test_ops_extract_orchestrator.py tests/ops_extract/test_parallel_pipeline.py tests/test_run_task_ops_extract_mode.py`
- 結果（成功/失敗、件数）
  - 成功: `12 passed`
- 学習・再発防止
  - traceは「実行されたstage」だけでなく「未実行stage」の理由（`skipped`）も残すと後段の原因分析が速い
  - crash dumpは失敗時のみ書き込むことで通常runのノイズを抑えつつ調査情報を確保できる
- 次段の着手条件
  - `pdf_diagnosis` 出力、needs_ocr複合判定、正規化ハッシュ、図表抽出best-effort契約を追加してテスト固定

### 2026-02-13 / Stage 5: Extract強化（Diagnosis/OCR判定/正規化証跡）
- 日時
  - 2026-02-13
- 段階名
  - Stage 5: `pdf_diagnosis` + `needs_ocr` 複合指標 + hash証跡
- 実装差分
  - `jarvis_core/ops_extract/pdf_diagnosis.py` を追加し `text-embedded/image-only/hybrid/encrypted/corrupted` 判定を実装
  - `orchestrator.py` で `ingestion/pdf_diagnosis.json` を常時出力（失敗時も空構造で作成）
  - `needs_ocr.py` を拡張し `unicode_category_distribution` と `extraction_exceptions`（`parser_fail/encoding_fail`）を判定材料へ追加
  - `orchestrator.py` の OCRメタを `engine_version/args/timings/per_page_stats` 付きに拡張
  - 正規化前後のハッシュを `metrics.extract.raw_text_sha256 / normalized_text_sha256` に保存
  - 図表抽出は best-effort 契約として `FIGURE_TABLE_EXTRACTION` warning に `success/failed/not_supported` を必ず記録
  - `contracts.py` に `ingestion/pdf_diagnosis.json` を optional artifact として追加
  - 新規テスト: `tests/ops_extract/test_pdf_diagnosis.py`, `tests/ops_extract/test_normalization_hashes.py`
  - 既存 `tests/ops_extract/test_needs_ocr.py` を拡張
- 実行コマンド
  - `uv run pytest -q tests/ops_extract/test_pdf_diagnosis.py tests/ops_extract/test_needs_ocr.py tests/ops_extract/test_normalization_hashes.py tests/ops_extract/test_ops_extract_orchestrator.py tests/ops_extract/test_trace_contract.py`
- 結果（成功/失敗、件数）
  - 成功: `19 passed`
- 学習・再発防止
  - OCR判定は閾値だけだと誤判定が残るため、例外種別と文字種分布を併用した方が失敗要因をwarningsへ説明可能
  - 失敗時でも `pdf_diagnosis.json` を必ず生成しておくと後続の契約検証が安定する
- 次段の着手条件
  - `stage_cache.json` を導入して hash一致skip / 不一致再計算 (`RECOMPUTED`) を実装し、determinismテストを追加

### 2026-02-13 / Stage 6: Resume/Determinism（重複処理防止）
- 日時
  - 2026-02-13
- 段階名
  - Stage 6: `stage_cache.json` と determinism 証明
- 実装差分
  - `jarvis_core/ops_extract/stage_cache.py` を追加し、`input_hash`・`outputs(sha256)`・`status`・`updated_at` を管理
  - `orchestrator.py` の `normalize_text` stageで cache判定を実装
    - hash一致 + 出力hash一致で skip
    - 不一致時は再計算し `RECOMPUTED` warning を記録
  - `stage_cache.json` を run成果物として常時出力
  - fixed-timeモード（`JARVIS_OPS_EXTRACT_FIXED_TIME`）を `orchestrator` / `drive_sync` / `failure_analysis` に導入し、再現性テストを安定化
  - `drive_sync.py` の同期対象に `trace.jsonl`, `stage_cache.json`, `ingestion/pdf_diagnosis.json` を追加
  - 新規テスト: `tests/ops_extract/test_stage_cache_resume.py`, `tests/ops_extract/test_ops_extract_determinism.py`
- 実行コマンド
  - `uv run pytest -q tests/ops_extract/test_stage_cache_resume.py tests/ops_extract/test_ops_extract_determinism.py tests/ops_extract/test_contract_schemas.py tests/ops_extract/test_trace_contract.py tests/ops_extract/test_ops_extract_orchestrator.py`
- 結果（成功/失敗、件数）
  - 成功: `11 passed`
- 学習・再発防止
  - stage cacheは「入力hash一致」だけでは不十分で、出力hashの照合まで入れると壊れたキャッシュを回避できる
  - determinismは時刻固定だけでなく run_duration/trace duration を0化する実装が必要
- 次段の着手条件
  - Drive同期を resumable upload 対応 client に切り替え、`sync_state v2` と二段階commitをエミュレータテストで証明する

### 2026-02-13 / Stage 7: Drive同期（resumable + commit protocol）
- 日時
  - 2026-02-13
- 段階名
  - Stage 7: ops_extract専用 Drive client と `sync_state v2`
- 実装差分
  - `jarvis_core/ops_extract/drive_client.py` を追加し resumable upload client（Google互換/エミュレータ両対応）を実装
  - `drive_sync.py` を `DriveResumableClient` 利用へ切替
    - 追加引数: `api_base_url`, `upload_base_url`, `chunk_bytes`, `resume_token`
    - `uploaded_files[]` に `file_id/session_uri/verified/attempts` を保持
    - 二段階commit（manifest draft→final）を維持
    - 失敗ファイル優先の再開ロジックを「優先順のみ」に修正（他pendingも取りこぼさない）
  - `orchestrator.py` から新引数を接続（config経由）
  - `tests/ops_extract/test_drive_resumable_emulator.py` を追加（途中失敗→再開→`committed_drive=true`）
  - `tests/ops_extract/test_drive_real_smoke.py` を追加（`@pytest.mark.network`、env必須で任意実行）
- 実行コマンド
  - `uv run pytest -q tests/ops_extract/test_drive_resumable_emulator.py`
  - `uv run pytest -q tests/ops_extract/test_sync_resume_commit.py tests/ops_extract/test_preflight_learning_sync_retention.py tests/ops_extract/test_drive_real_smoke.py`
- 結果（成功/失敗、件数）
  - 成功: `1 passed`（emulator）
  - 成功: `14 passed, 1 skipped`（real smokeはenv未設定でskip）
- 学習・再発防止
  - resume実装は「failed対象のみ再送」にすると partial upload で未送信ファイルを残すため、failed優先の順序制御に留める必要がある
  - エミュレータで `500→再開` を強制すると commit protocol の欠陥を早期に検出できる
- 次段の着手条件
  - config versioning / migration / secrets redaction / CI security gate を追加し、互換性と運用安全性をテスト固定する

### 2026-02-13 / Stage 8: 互換性・移行・セキュリティ・運用自動化
- 日時
  - 2026-02-13
- 段階名
  - Stage 8: config versioning + migration + secret安全化 + CI guard
- 実装差分
  - `contracts.py` に `OPS_EXTRACT_CONFIG_SCHEMA_VERSION` と deprecated key対応を追加
    - `sync_chunk_size`, `drive_api_url`, `drive_upload_url`, `trace`, `resume` を後方互換で吸収
  - `security.py` を追加し、機微情報マスク（token/Bearer）を実装
  - `orchestrator.py` の `run_metadata.config` をマスク済み出力へ変更（Drive token露出防止）
  - `drive_sync.py` の `last_error` を redaction して保存
  - `scripts/migrate_ops_extract_runs_v1_to_v2.py` を追加し、manifest/sync_state/stage_cache/trace/pdf_diagnosis の移行を自動化
  - CI (`.github/workflows/ci.yml`) に `uv lock --check` と security job強化（`bandit`, `pip-audit` fail-fast）を追加
  - 新規テスト:
    - `tests/ops_extract/test_config_versioning.py`
    - `tests/ops_extract/test_migration_v1_to_v2.py`
    - `tests/security/test_ops_extract_secrets_redaction.py`
- 実行コマンド
  - `uv run pytest -q tests/ops_extract/test_config_versioning.py tests/ops_extract/test_migration_v1_to_v2.py tests/security/test_ops_extract_secrets_redaction.py`
- 結果（成功/失敗、件数）
  - 成功: `5 passed`
- 学習・再発防止
  - run_metadataへconfigをそのまま書くと秘密情報が残るため、保存時の一律redactionが必須
  - migrationは「既存ファイルの部分補完」にすると再実行しても壊れない（idempotent）
- 次段の着手条件
  - 最終受け入れ用 `tests/e2e/test_ops_extract_proof_driven.py` を追加し、text/ocr/drive-resume の3経路を固定化して全体ゲートを実行

### 2026-02-13 / Stage 9: 最終統合と受け入れゲート
- 日時
  - 2026-02-13
- 段階名
  - Stage 9: Proof-Driven E2E固定 + 最終品質ゲート
- 実装差分
  - `tests/e2e/test_ops_extract_proof_driven.py` を追加
    - E2E-1: text-embedded 経路（OCR不要）
    - E2E-2: image-only 相当経路（OCR必要、OCR I/O契約実ファイル）
    - E2E-3: Drive同期（エミュレータで失敗→再開→commit）
  - `release.yml` に ops_extract proof-driven guard（no-stub + contract/emulator/e2e）を追加
  - `tests/ops_extract/test_determinism.py` は既存同名テストとの衝突回避のため `tests/ops_extract/test_ops_extract_determinism.py` に改名
- 実行コマンド
  - `uv run pytest -q tests/e2e/test_ops_extract_proof_driven.py`
  - `uv run pytest -q tests/ops_extract tests/security/test_ops_extract_secrets_redaction.py tests/e2e/test_ops_extract_proof_driven.py tests/test_run_task_ops_extract_mode.py`
  - `uv run pytest -q`
  - `uv run ruff check jarvis_core tests`
  - `uv run black --check jarvis_core tests`
  - `uv run mypy --explicit-package-bases --follow-imports=skip jarvis_core/evidence/ jarvis_core/contradiction/ jarvis_core/citation/ jarvis_core/sources/ --ignore-missing-imports`
  - `uv build`
- 結果（成功/失敗、件数）
  - 成功: E2E proof-driven `3 passed`
  - 成功: ops_extract/security/e2e統合 `60 passed, 1 skipped`
  - 成功: 全体 `6457 passed, 469 skipped`
  - 成功: ruff / black / mypy / build
- 学習・再発防止
  - 大規模リポジトリではテストファイルのbasename衝突で収集エラーが起きるため、ドメイン名を含む命名（`test_ops_extract_*`）が安全
  - release前ガードに emulator + contract を入れることで「動いたふり」の混入を抑止できる
- 次段の着手条件
  - Proof-Driven v2.0 実装完了。以後は実運用データで閾値（needs_ocr/retention/retry）を調整する段階
