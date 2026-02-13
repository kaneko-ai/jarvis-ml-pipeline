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
