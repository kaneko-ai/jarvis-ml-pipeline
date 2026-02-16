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


## Harvest Watch/Work 運用 (Run-Scoped Queue)

### watch
```bash
jarvis harvest watch --source pubmed --query "immunotherapy" --since-hours 6 --budget "max_items=200,max_minutes=30,max_requests=400" --out logs/runs --out-run auto
```

### work
```bash
jarvis harvest work --budget "max_items=200,max_minutes=30,max_requests=400" --out logs/runs --out-run <same_run_id>
```

運用ルール:
- queueは run単位で永続化する: `logs/runs/{run_id}/harvest/queue.jsonl`
- `watch` と `work` は同一 `run_id` で継続する
- budget超過時は `result.json.status=needs_retry` とし、詳細は `harvest/report.md` / `eval_summary.json` に残す
- offline時は成功扱いにしない（`failed` または `needs_retry`）
