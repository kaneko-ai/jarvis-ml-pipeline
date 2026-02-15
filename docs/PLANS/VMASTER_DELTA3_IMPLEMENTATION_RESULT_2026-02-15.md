> Authority: DECISIONS (Level 2, Binding)

# vMASTER-Δ3.0 Implementation Result

- Date: 2026-02-15 16:40:00 +09:00
- Branch: `main`
- Scope: `vMASTER-Δ3.0` (G1/G2/G3/G4)

## 1. 実装結果（事実）

### G1: 契約矛盾の解消
- `validate_run_contracts_strict(..., assume_failed=True)` の契約を維持し、`orchestrator` 側の失敗時再検証経路は既存実装を維持。
- 契約失敗時の `crash_dump` 前提の閉路が壊れていないことを既存テストで確認。

### G2: Drive post-audit
- `drive_audit` / `javisctl audit --run-id` / `remote_root_folder_id` 連携は既存実装を維持。
- 追加実装なしで、欠損検知E2Eを回帰確認。

### G3: Personal Ops Dashboard + telemetry/progress拡張
- 新規: `jarvis_core/ops_extract/dashboard/actions.py`
- 改修: `jarvis_core/ops_extract/dashboard/app.py` を personal-first UI へ更新
  - latest追従
  - Queue summary
  - Quick Actions（sync/doctor/audit/open folder）
  - 24h snapshot / telemetry / progress / ETA / confidence / papers counters
- 改修: `jarvis_core/ops_extract/telemetry/progress.py`
  - `paper_counter` 連携 (`papers_total` / `papers_run`) を追加
- 改修: `jarvis_core/ops_extract/telemetry/models.py`
  - `ProgressPoint` に paper counter フィールドを追加

### G4: Paper Counter + Drive Connect + Runbook
- 新規: `jarvis_core/literature/paper_counter.py`
  - `init_if_missing` / `bump` / `snapshot`
  - `os.replace` による原子更新
- 新規: `jarvis_core/ops_extract/personal_config.py`
  - 環境変数 → `~/.config/javis/config.json` → `config/javis.json` 読み込み
- 新規: `jarvis_core/ops_extract/drive_auth_flow.py`
  - InstalledAppFlow によるローカルOAuth
- 改修: `jarvis_core/ops_extract/oauth_google.py`
  - token cache 内の refresh/client_id/client_secret だけで再取得可能
- 改修: `jarvis_core/ops_extract/cli/javisctl.py`
  - `drive-auth`, `drive-whoami` 追加
  - `dashboard --run-id latest` 対応
  - personal config 既定値利用
- 改修: `scripts/javis_dashboard.py`
  - `--run-id latest` 解決
- 新規: `docs/RUNBOOK_PERSONAL.md`

## 2. 追加/更新テスト

- `tests/ops_extract/test_personal_config_loads_defaults.py`
- `tests/literature/test_paper_counter_atomic_bump.py`
- `tests/literature/test_pdf_download_bumps_counter.py`
- `tests/ops_extract/test_oauth_google_uses_cached_refresh_token.py`
- `tests/test_dashboard_personal_smoke.py`

## 3. 実行ログ（事実）

- `uv run pytest -q`
  - **6508 passed, 469 skipped, 20 warnings**
- `uv run pytest tests/ops_extract tests/e2e/test_ops_extract_proof_driven.py -q`
  - **82 passed, 1 skipped**
- `uv run ruff check jarvis_core tests scripts`
  - Pass
- `uv run black --check jarvis_core tests scripts`
  - Pass
- `uv run python scripts/no_stub_gate.py --paths jarvis_core/ops_extract`
  - Pass
- `uv run python scripts/detect_garbage_code.py`
  - Pass
- `uv run python scripts/security_gate.py`
  - Pass
- `uv run --with build python -m build jarvis-ml-pipeline`（repo親ディレクトリから）
  - Pass

## 4. 事実ベーススコア

### 4.1 Gate Score
- 評価ゲート: 8
  - pytest(full), pytest(ops_extract), ruff, black, no_stub, garbage_check, security_gate, build
- Pass: 8
- Fail: 0
- Score: **100 / 100**

### 4.2 Warning Score
- pytest warnings: 20（全件が `pathlib.Path.link_to` deprecation）
- Runtime regression warnings: 0（今回差分由来は確認されず）
- Score: **96 / 100**

### 4.3 Δ3 Completion Score
- G1: 完了
- G2: 完了
- G3: 完了
- G4: 完了
- Score: **100 / 100**

