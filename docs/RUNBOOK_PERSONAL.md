> Authority: ROADMAP (Level 5, Non-binding)

# Personal Runbook (Ops+Extract)

## 1. セットアップ
```bash
uv sync
uv pip install -e ".[dashboard,drive_auth]"
```

## 2. Google Drive 認証
```bash
javisctl drive-auth --client-secrets ~/Downloads/client_secret.json
javisctl drive-whoami
```

## 3. ops_extract 実行（必要ならDrive同期）
```bash
javisctl run --project ops --inputs <pdf1> <pdf2> --sync-enabled
```

## 4. ダッシュボード起動（最新run追従）
```bash
javisctl dashboard --run-id latest
```

## 5. キューが溜まった時
- ダッシュボードの `Sync queue now` を押す
- またはCLI:
```bash
javisctl sync --queue-dir logs/sync_queue
```

## 6. 監査・診断
```bash
javisctl audit --run-id <run_id>
javisctl doctor --queue-dir logs/sync_queue
```

## 期待される成果物チェック
- `logs/runs/<run_id>/manifest.json`
- `logs/runs/<run_id>/sync_state.json`
- `logs/runs/<run_id>/telemetry.jsonl`
- `logs/runs/<run_id>/progress.jsonl`
- `logs/runs/<run_id>/drive_audit.json`（audit実行時）
- `logs/counters/papers.json`

