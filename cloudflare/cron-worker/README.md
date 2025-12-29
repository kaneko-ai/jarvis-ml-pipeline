# Jarvis Cron Enqueuer (Cloudflare Worker)

Cloudflare Cron Triggers で定期的に Jarvis API の `POST /api/jobs` を叩き、
`collect_and_ingest` ジョブを自動投入するための Worker です。

## 前提

- Cron は **UTC** 基準で実行されます（JST ではありません）。
- `JARVIS_API_BASE` は末尾スラッシュなし推奨（Worker 側でも除去します）。
- Jarvis API は **外部から HTTPS で到達可能**である必要があります（少なくとも `/api/jobs`）。

## Cloudflare 側セットアップ（ローカルから）

```bash
cd cloudflare/cron-worker
npm install
# Vars
npx wrangler secret put JARVIS_API_TOKEN
# → token入力
npx wrangler deploy
```

その後、Cloudflare Dashboard で `JARVIS_API_BASE` を本番 URL に設定するか、
`wrangler.toml` の `vars` を編集して再 deploy してください。

## API 側セットアップ（本番）

- 環境変数 `API_TOKEN` を設定（Worker に入れた token と一致させる）
- 例:
  - `API_TOKEN=...`
  - `REDIS_URL=...`（RQ/Redis を使うなら）
- API 再起動

## 動作確認（必須）

1. Worker を `DRY_RUN=1` にして一度 cron 相当を手動実行（ログ確認）
2. `DRY_RUN=0` に戻す
3. 次の cron 時刻後、API ログに `/api/jobs` が来ていること
4. UI の Jobs 一覧で `source=cloudflare_cron` / `target_name` が付いたジョブが増えること
5. 完了後 CD73 で検索して結果が増えること

## トラブルシュートのヒント

- **投入は成功したが実行されない**: RQ worker が動いていない、Redis 接続が死んでいる等。
  UI と API ログで検出できるようにしてください。
- **API がプライベートネットワークのみ**: Worker から叩けません。
  API は外部から HTTPS で到達可能にしてください。
