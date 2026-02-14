> Authority: DECISIONS (Level 2, Binding)

# vMASTER-Δ2.0 Implementation Result

- Date: 2026-02-15 01:52:26 +09:00
- Branch: `feat/vmaster-delta2-opsextract`
- Scope: `vMASTER-Δ2.0` (G1/G2/G3 + P0-P6)

## 1. 実装結果

### G1: 契約の最終矛盾（crash_dumpタイミング）
- `validate_run_contracts_strict(..., assume_failed: bool = False)` を追加
- `orchestrator` で contract error 発生時に `crash_dump.json` 出力後の再検証を追加
- 再検証で `missing:crash_dump.json` 以外の残差がある場合、`crash_dump.json` に `post_contract_validation_errors` を追記

### G2: Drive post-audit
- `jarvis_core/ops_extract/drive_audit.py` を追加
- `manifest.outputs` を基準に remote 存在・size・md5 を監査
- `drive_sync` で `remote_root_folder_id` を `sync_state.json` に保存
- `javisctl audit` を `--run-id` / `--run-dir` 対応へ拡張

### G3: telemetry / progress / ETA / dashboard
- 追加: `jarvis_core/ops_extract/telemetry/{models,sampler,progress,eta}.py`
- `orchestrator` に telemetry/progress emit を統合（finally で sampler 停止）
- fixed-time モードでは determinism 維持のため telemetry/progress を抑止
- 追加: `jarvis_core/ops_extract/dashboard/app.py`（Streamlit + Plotly）
- 追加: `scripts/javis_dashboard.py`
- 追加: `javisctl dashboard`
- `pyproject.toml` に optional extras `dashboard` を追加

### P5: 論文サーベイ進捗％（canonical + cli_v4）
- `run_literature_to_plan(..., progress_emitter=None)` を追加
- `cli_v4` から ProgressEmitter を渡し、4 stage を記録
  - `survey_discover`
  - `survey_download`
  - `survey_parse`
  - `survey_index`

### P0: 変更前自己診断
- 追加: `scripts/audit_repo_state.py`
- 追加: `tests/ops_extract/test_audit_repo_state_runs.py`
- 出力: `reports/audit_repo_state.md`

## 2. 追加/更新テスト（今回差分）
- `tests/ops_extract/test_audit_repo_state_runs.py`
- `tests/ops_extract/test_contract_strict_assume_failed_requires_crash_dump.py`
- `tests/e2e/test_drive_audit_detects_missing.py`
- `tests/ops_extract/test_progress_emitter_writes_jsonl.py`
- `tests/ops_extract/test_telemetry_sampler_graceful_without_psutil.py`
- `tests/literature/test_survey_emits_progress.py`

## 3. 実行ログ（事実）
- `uv run pytest -q`
  - Result: `6502 passed, 469 skipped`
- `uv run pytest tests/ops_extract tests/e2e/test_ops_extract_proof_driven.py -q`
  - Result: `80 passed, 1 skipped`
- `uv run ruff check jarvis_core tests scripts`
  - Result: Pass
- `uv run black --check jarvis_core tests scripts`
  - Result: Pass
- `uv run python -m build`
  - Result: Pass
- `uv run python tools/spec_lint.py`
  - Result: `Checked 8 files / PASS`
- `uv run python scripts/security_gate.py`
  - Result: Fail（`pip-audit` 実行中の外部通信断: `ConnectionResetError WinError 10054`）

## 4. 事実ベーススコア

### 4.1 Gate Score
- 評価対象ゲート: 7
  - pytest(full), pytest(ops_extract), ruff, black, build, spec_lint, security_gate
- Pass: 6
- Fail: 1
- Score: **85.7 / 100**

### 4.2 vMASTER-Δ2.0 Goal Score
- G1: 完了
- G2: 完了
- G3: 完了
- Score: **3 / 3 (100%)**

## 5. 残課題
- `security_gate` の `pip-audit` がネットワーク要因で不安定
- 本体コード不整合ではなく外部到達性が要因
- 対応候補:
  - `pip-audit` への retry/backoff 導入
  - CI での PyPI 到達性チェック先行

## 6. 補足
- Spec Lint failure の原因だった `docs/PLANS/QUALITY_HARDENING_FINAL_2026-02-14.md` の Authority Header 改行崩れを修正済み。
