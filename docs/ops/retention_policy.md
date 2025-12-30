# Run Retention Policy

## 目的

`public/runs/` に生成される実行結果が増え続けると、GitHubリポジトリが肥大化し続けて運用が破綻します。
このポリシーは長期運用でもリポジトリサイズが指数的に増えないようにするためのものです。

## 保持方針（デフォルト）

`public/runs/<run_id>/` を対象に、次のどちらか（両方指定時は厳しい方）で保持します。

- `KEEP_DAYS=14`
- `KEEP_LAST=50`

`KEEP_DAYS` と `KEEP_LAST` の両方が指定されている場合は、**両方を満たすもののみ保持**します。
つまり「直近の日数内であり、かつ最新N件以内」の条件を満たさない run は削除対象になります。

## アーカイブと削除

削除対象の run はディレクトリごと削除されます。
削除前に `manifest.json` から最小限の情報を取り出し、
`public/runs/archive_index.jsonl` に追記して監査可能にします。

## 重要: 復元不可

`public/runs/<run_id>/` の削除は **復元不可** です。
削除後は `archive_index.jsonl` に残された情報のみが唯一の記録となります。

## 運用スクリプト

- 実行: `scripts/prune_runs.py`
- 影響: 削除後に `scripts/build_runs_index.py` を実行して `public/runs/index.json` を再生成すること。
