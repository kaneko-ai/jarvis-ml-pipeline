# HANDOVER_v17.md — JARVIS ML Pipeline 引き継ぎ書

> **作成日**: 2026-03-06 06:00 JST
>
> **作成者**: Claude Opus 4.6 + kaneko yu
>
> **前回引き継ぎ**: HANDOVER_v16.md
>
> **対象**: AI（Claude / GPT / Codex）
>
> **GitHub**: https://github.com/kaneko-ai/jarvis-ml-pipeline (main ブランチ)
>
> **関連リポジトリ**: https://github.com/kaneko-ai/zotero-doi-importer

---

## 0. この文書の読み方

この引き継ぎ書 1 枚でプロジェクトの「環境・構成・完了済み作業・未完了タスク・既知の問題・絶対ルール」をすべて把握できる。過去の HANDOVER_v1〜v16 を読む必要はない。

---

## 1. プロジェクト概要

**JARVIS ML Pipeline** は 2 つのサブシステムで構成される AI 研究支援プラットフォームである。

### 1-A. Python CLI バックエンド (v2.0.0, tag: v2.0.0)

- 22 の CLI コマンド（search, pipeline, evidence, score, screen, browse, skills, mcp, orchestrate, obsidian-export, semantic-search, contradict, zotero-sync, pdf-extract, deep-research, citation-graph, citation, citation-stance, prisma, merge, note, run）
- PubMed / Semantic Scholar / OpenAlex / arXiv / Crossref から論文検索
- CEBM エビデンスグレーディング、ペーパースコアリング、矛盾検出
- ChromaDB ベクトル検索（~36 論文インデックス済み）
- LangGraph 6 エージェントオーケストレーター
- LiteLLM 統一 LLM アクセス（Gemini / OpenAI / DeepSeek）
- Obsidian ノート自動生成、Zotero 同期、PRISMA ダイアグラム、BibTeX 出力
- pytest 50 テスト全パス

### 1-B. Agent-Web フロントエンド (Node.js/Express)

- Express v5 + better-sqlite3 + SSE ストリーミング
- 3 タブ UI（Chat | Pipeline | Monitor）+ メモリ UI パネル + レスポンシブレイアウト
- Daily Digest: 5 キーワード自動論文収集 → Gemini 要約 → SQLite 保存 → Obsidian 出力
- パイプライン: 7 ステップ SSE（検索→重複除去→スコアリング→ソート→Gemini 要約→JSON 生成→DB 保存+PDF アーカイブ）
- セッションメモリ（H-2）: 直近 20 メッセージをコンテキストとして送信
- 永続メモリ（H-3）: facts / user_preferences テーブルでクロスセッション記憶
- Memory API + Memory Management UI（facts CRUD, preferences, context 表示）
- チャット UI 強化: reasoning trace 表示、JSON ハイライト、inline code、DOI/PMID auto-link、折りたたみ Markdown 見出し
- テーマ: light/dark toggle を CSS custom properties ベースで実装
- テスト: **54 テスト全パス**（E2E 7 テストを含む）

---

## 2. 環境情報（2026-03-06 時点で動作確認済み）

| 項目 | 値 |
|---|---|
| OS | Windows 11 |
| Node.js | v24.13.1 |
| npm | 11.8.0 |
| Python | 3.11.9（.venv）/ 3.12.3（venv、旧） |
| Git | 設定済み（safe.directory 登録済み） |
| プロジェクトルート | `C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline` |
| agent-web ルート | `C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline\agent-web` |
| Python venv | `C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline\.venv` |
| Obsidian Vault | `H:\obsidian-vault`（config.yaml: `H:\\obsidian-vault`） |
| データ保存先 | `H:\jarvis-data\`（logs, exports, pdf-archive, digests） |
| GitHub | `https://github.com/kaneko-ai/jarvis-ml-pipeline.git` (main) |
| ポート | 3000（Express）, 4141（Copilot API）, 8501（Streamlit, 待機） |
| LLM | gemini-2.0-flash（デフォルト）, claude-sonnet-4.6（チャット）, gpt-4.1, o4-mini |
| Codex App | 3 エージェント（explorer, worker, reviewer）定義済み |
| C: ドライブ空き | ~45 GB |
| H: ドライブ | Google Drive 2 TB（使用 57 GB） |

### .env ファイル（プロジェクトルート直下、1 ファイルのみ — .gitignore 済み）

Copy

ZOTERO_API_KEY=wc3GxeCPThtkWJnvVJQsLtLb ZOTERO_USER_ID=16956010 OPENAI_API_KEY=（空） DEEPSEEK_API_KEY=（空） LLM_MODEL=gemini/gemini-2.0-flash DATALAB_API_KEY=ng2yRJcuRfpvc0mCRwENWwGucyfLq5eTOXMTBB7eeyY GEMINI_API_KEY=AIzaSyCK...（実値は .env 参照）

### config.yaml（プロジェクトルート直下）

```yaml
obsidian:
  vault_path: "H:\\obsidian-vault"
  papers_folder: JARVIS/Papers
  notes_folder: JARVIS/Notes
zotero:
  api_key: ''
  user_id: ''
  collection: JARVIS
search:
  default_sources: [pubmed, semantic_scholar, openalex]
  max_results: 20
llm:
  default_provider: gemini
  default_model: gemini/gemini-2.0-flash
  fallback_model: openai/gpt-4.1
  models:
    gemini: gemini/gemini-2.0-flash
    openai: openai/gpt-5-mini
    deepseek: deepseek/deepseek-reasoner
  cache_enabled: true
  max_retries: 3
  temperature: 0.3
evidence:
  use_llm: false
  strategy: weighted_average
storage:
  logs_dir: "H:\\jarvis-data\\logs"
  exports_dir: "H:\\jarvis-data\\exports"
  pdf_archive_dir: "H:\\jarvis-data\\pdf-archive"
  local_fallback: logs
digest:
  keywords:
    - "CRISPR gene therapy"
    - "PD-1 immunotherapy"
    - "PD-1"
    - "spermidine"
    - "cancer"
  schedule_hour: 7
  schedule_minute: 0
  papers_per_keyword: 10
  summarize_top_n: 5
  output_dir: "agent-web/data/digests"
```

## 3. ディレクトリ構成（主要部分）

```text
jarvis-ml-pipeline/
├── .env                              # API キー（GEMINI_API_KEY 等）
├── .gitignore
├── config.yaml                       # 全体設定
├── README.md                         # v2.0.0 ドキュメント（Agent-Web 含む）
├── run-daily-digest.bat              # タスクスケジューラ用バッチ
├── HANDOVER_v17.md                   # ★ この文書
├── HANDOVER_v16.md
├── .github/
│   └── workflows/
│       └── test.yml                  # CI/CD（GitHub Actions）
├── .codex/
│   └── agents/
│       ├── explorer.toml
│       ├── worker.toml
│       └── reviewer.toml
├── jarvis_cli/                       # Python CLI（22 コマンド）
├── jarvis_core/                      # Python コアライブラリ
│   ├── embeddings/                   # ChromaDB PaperStore
│   ├── evidence.py                   # CEBM エビデンスグレーディング
│   ├── llm/                          # LiteLLM クライアント
│   ├── mcp/                          # MCP Hub（5 サーバー, 15 ツール）
│   ├── pdf/                          # PDF→Markdown
│   ├── rag/                          # LightRAG, CitationGraph
│   ├── sources/                      # 統合論文検索
│   └── storage_utils.py              # H: ドライブ / ローカルフォールバック
├── jarvis_web/                       # Streamlit ダッシュボード
├── tests/                            # pytest（50 テスト）
└── agent-web/                        # ★ Node.js Web アプリ
    ├── package.json                  # ESM, test:ci に e2e を含む
    ├── data/
    │   ├── *.json                    # パイプライン結果
    │   └── digests/                  # Daily Digest 出力
    ├── public/
    │   ├── index.html                # 3 タブ SPA + Memory UI + theme toggle
    │   ├── css/styles.css            # テーマ、レスポンシブ、アニメーション、citation UI
    │   └── js/app.js                 # フロントエンド（Memory UI, reasoning trace, markdown 強化）
    ├── src/
    │   ├── server.js                 # Express v5 エントリポイント
    │   ├── db/
    │   │   ├── database.js           # sessions + messages テーブル
    │   │   ├── jarvis.db             # SQLite DB ファイル
    │   │   ├── papers-repository.js  # papers CRUD
    │   │   ├── memory-store.js       # facts + user_preferences
    │   │   ├── chroma-bridge.js      # Python ChromaDB 連携
    │   │   └── create-papers-table.js
    │   ├── routes/
    │   │   ├── chat.js               # /api/chat/stream
    │   │   ├── pipeline.js           # 7 ステップ SSE + DB 保存 + PDF アーカイブ
    │   │   ├── digest.js
    │   │   ├── monitor.js
    │   │   ├── memory.js
    │   │   ├── sessions.js
    │   │   ├── models.js
    │   │   ├── skills.js
    │   │   ├── mcp.js
    │   │   └── usage.js
    │   └── skills/
    │       ├── daily-digest.js
    │       ├── digest-to-obsidian.js
    │       ├── pdf-archiver.js
    │       ├── zotero-sync.js
    │       └── skill-registry.js
    └── tests/
        ├── database.test.js
        ├── api.test.js
        ├── digest.test.js
        ├── pipeline.test.js
        ├── monitor.test.js
        ├── gemini-summarizer.test.js
        ├── parallel-runner.test.js
        └── e2e.test.js               # E2E 7 テスト
```

## 4. API エンドポイント一覧

| メソッド | パス | 説明 | 状態 |
|---|---|---|---|
| POST | /api/chat/stream | チャット（SSE + メモリ統合） | ✅ |
| GET | /api/sessions | セッション一覧 | ✅ |
| GET | /api/models | LLM モデル一覧 | ✅ |
| GET | /api/skills | スキル一覧 | ✅ |
| GET/POST | /api/mcp/* | MCP ブリッジ | ✅ |
| GET | /api/usage | 使用量 | ✅ |
| GET | /api/pipeline/run?query=…&limit=… | パイプライン実行（SSE 7 ステップ） | ✅ |
| GET | /api/pipeline/history | パイプライン履歴 | ✅ |
| GET/POST | /api/digest/run | Daily Digest 実行（SSE） | ✅ |
| GET | /api/digest/history | Digest 履歴 | ✅ |
| GET | /api/digest/report/:filename | Digest レポート取得 | ✅ |
| GET | /api/monitor/status | システム状態 | ✅ |
| GET | /api/monitor/health | ヘルスチェック | ✅ |
| GET | /api/monitor/history | Monitor 履歴 | ✅ |
| GET | /api/memory/facts | 全 facts 取得 | ✅ |
| GET | /api/memory/facts/:key | 単一 fact 取得 | ✅ |
| POST | /api/memory/facts | fact 保存 | ✅ |
| DELETE | /api/memory/facts/:key | fact 削除 | ✅ |
| GET | /api/memory/preferences | 全 preferences 取得 | ✅ |
| POST | /api/memory/preferences | preference 保存 | ✅ |
| GET | /api/memory/context | メモリコンテキスト取得 | ✅ |
| GET | /api/health | 簡易ヘルス | ✅ |
| — | /data/* | 静的 JSON 配信 | ✅ |

## 5. 完了済み全タスク

Phase 0: 環境構築 ✅

Codex App 3 エージェント定義、config 修正、Git safe.directory、better-sqlite3、paper-search.js 動作確認、.har 除去

Phase 1: コア機能 ✅

3 タブ UI、parallel-runner.js、pipeline.js（SSE 7 ステップ）、monitor.js、Gemini 要約、エラーハンドリング、21 テスト全パス

Phase 2: Daily Digest ✅

- P2-1: Daily Digest 初回実行テスト成功（5 キーワード, 49 論文, 2026-03-05）
- P2-2: Windows タスクスケジューラ登録済み（毎日 07:00, 「JARVIS-DailyDigest」タスク確認済み）
- P2-3: Digest→Obsidian 自動出力（digest-to-obsidian.js）

Phase 3: データ管理 ✅

- P3-1: SQLite papers テーブル + CRUD（papers-repository.js, 9 関数: init, insertPaper, insertPapers, getPapers, getPaperByDoi, getPaperByPmid, searchPapers, countPapers, deletePaper）
- P3-2: 重複排除強化（titleSimilarity in pipeline.js）
- P3-3: PDF アーカイバ（pdf-archiver.js — Unpaywall + 直接ダウンロード）
- P3-4: Zotero 同期（zotero-sync.js — Zotero Web API v3）
- P3-5: ChromaDB ブリッジ（chroma-bridge.js — Python subprocess）
- パイプライン→DB 自動保存（pipeline.js 内で insertPapers 実行）
- パイプライン→PDF アーカイブ（best-effort, 失敗時は警告のみ）
- Daily Digest→Obsidian 自動出力（best-effort）

品質改善 ✅

- Gemini レートリミット対策: concurrency 1, delay 4500ms（15 RPM 以内で安全）
- API 429 リトライ: PubMed 350ms 遅延 + リトライ、S2 1500ms + 5 秒待ちリトライ（最大 2 回）
- パイプライン DB 保存: papers テーブルへ自動 INSERT
- GEMINI_API_KEY 未設定ガード（summarizeBatch 内）

H-2: セッションメモリ ✅

- chat.js に SYSTEM_PROMPT 定義、メッセージ順序 [system, …history, user] 統一
- 直近 20 メッセージをコンテキスト送信（buildHistory()）
- SQLite papers テーブルから研究キーワードに関連する上位 3 件を検索し、システムプロンプトに注入

H-3: 永続クロスセッションメモリ ✅

- memory-store.js: facts テーブル + user_preferences テーブル
- エクスポート関数: storeFact, getFact, getFactsByCategory, getAllFacts, deleteFact, setPreference, getPreference, getAllPreferences, getMemoryContext, extractAndStoreFacts
- chat.js 統合: getMemoryContext() でユーザー記憶をプロンプトに注入、extractAndStoreFacts() で応答からファクト抽出

Memory API ✅

- memory.js ルート: /api/memory/* エンドポイント 7 つ
- server.js に memoryRouter 登録済み

Session 2026-03-06 (Post-v16) ✅

- MEM-1: Memory Management UI panel（facts CRUD, preferences, context display）
- README-1: README.md updated to v2.0.0 with full Agent-Web docs
- UI-3: Responsive layout with mobile sidebar toggle
- UI-4: Markdown rendering improvements（collapsible h2/h3）
- UI-5: Fade-in animations（messages, timeline, cards）
- E2E-1: End-to-end integration tests（+7 tests, total 54）
- UI-6: Reasoning trace display for SSE streaming steps
- THEME-1: Light/dark theme toggle with CSS custom properties
- CHAT-1: JSON syntax highlight, inline code, DOI/PMID auto-links

テスト状況 ✅

- agent-web: 54/54 テスト合格（2026-03-06 時点）
- Python: 50/50 pytest 合格

Daily Digest 実行実績

| 日付 | キーワード数 | 論文数 | JSON サイズ | MD サイズ |
|---|---:|---:|---:|---:|
| 2026-03-05 | 5 | 49 | 4977 B | 3611 B |
| 2026-03-06 | 5 | 49 | 4459 B | 3027 B |

## 6. 未実施タスク（優先度順）

高優先度 🔴

| ID | タスク | 備考 |
|---|---|---|
| CHAT-2 | PDF viewer in chat | PDF リンクをカード表示し、chat 内で PDF 関連導線を強化 |
| PIPE-UI | Pipeline results UI | 進捗バー、paper cards、summary など結果表示の強化 |
| P3-6 | LightRAG Web bridge | jarvis_core の LightRAG を Agent-Web に接続。graph persistence で asyncio.CancelledError の既知問題あり |

中優先度 🟡

| ID | タスク | 備考 |
|---|---|---|
| WS-1 | WebSocket migration | SSE → WebSocket（双方向通信） |
| RC-1 | Remote control API | 外部トリガー・統合用 API 層 |
| DASH-1 | Dashboard / analytics view | paper counts, digest stats, trend 可視化 |
| SEARCH-UI | Advanced search UI with filters | source / date / score / evidence filter を持つ検索 UI |

低優先度 🟢

| ID | タスク | 備考 |
|---|---|---|
| EXPORT-1 | Export chat history as Markdown/PDF | 会話と補助データのエクスポート |
| NOTIF-1 | Browser notifications for digest completion | Digest 完了時のブラウザ通知 |

## 7. Git コミット履歴（直近主要）

- 880f85df docs: update README.md with Agent-Web Phase 3, Memory API, v2.0.0
- bf0a9155 feat(agent-web): add Memory management UI panel (MEM-1)
- e3ab473a feat(agent-web): responsive layout, fade-in animations, E2E tests (UI-3, UI-5, E2E-1) - 54 tests
- 7cbdb627 feat(agent-web): reasoning trace, light/dark theme toggle, JSON highlight + DOI/PMID links
- b01577dd feat: Phase 3 foundation - papers CRUD, digest-to-obsidian, CI workflow, rate limit fixes, pipeline DB save
- 4d6c7e9e feat: P3-3 PDF archiver, P3-4 Zotero sync, P3-5 ChromaDB bridge
- 643c7d74 feat(agent-web): Phase 1 UI – dark/gold, particles
- 3938883a feat(agent-web): session memory – H-2
- 37051d0d docs: add Agent-Web section – I-3
- 38587e79 feat: Agent-Web v1.0.0
- edd4d0cf (tag: v2.0.0) D7: v2.0.0 release

## 8. 既知の問題と注意事項

| 問題 | 深刻度 | 対処法 |
|---|---|---|
| npm test で spawn EPERM | 低 | Codex App サンドボックス内でのみ発生。PowerShell 直接実行では全パス。または `node --test --test-isolation=none tests/*.test.js` を使用 |
| OPENAI_API_KEY が空 | 低 | OpenAI 系機能は動作しない。gemini-2.0-flash で代替 |
| DEEPSEEK_API_KEY が空 | 低 | DeepSeek フォールバック不可 |
| claude-opus-4.6 で 400 エラー | 中 | claude-sonnet-4.6 を使用する |
| gpt-5.1 で 400 エラー | 中 | gpt-4.1 を使用する |
| Gemini レートリミット | 中 | 15 RPM 制限。concurrency 1, delay 4500ms で対策済み |
| Semantic Scholar レートリミット | 中 | 100 req/5 min。1500ms 遅延 + 429 リトライで対策済み |
| PubMed レートリミット | 低 | 3 req/s。350ms 遅延で対策済み |
| LightRAG asyncio.CancelledError | 中 | graph persistence 失敗。P3-6 で対応予定 |
| Datalab API 403 | 低 | PyMuPDF にフォールバック |
| H: ドライブ切断 | 低 | Google Drive が切断されると Obsidian / jarvis-data パスが無効に。再接続で復旧 |
| agents.py vs agents/ 競合 | 低 | `jarvis_core.agents.orchestrator` をインポートしない |
| Scrapling css_first 未定義 | 低 | browse.py 利用時に注意 |
| PowerShell で $1 消失 | 中 | JS 内の `$1` が PowerShell の here-string で消える。`String.fromCharCode(36)+"1"` または一時 `.js` ファイル経由で回避 |
| LF/CRLF 警告 | 低 | git push 時に表示される。動作影響なし |
| config.yaml Zotero api_key 空 | 低 | `.env` の ZOTERO_API_KEY とは別管理 |
| git-credential-manager-core rename warning | 低 | cosmetic only、ignore で可 |

## 9. 絶対ルール（必ず守ること）

agent-web 外のファイルを変更しない（Web タスクの場合）

python -c で複雑なコードを実行しない — 必ず .py ファイルを作成して実行

jarvis_cli/init.py は完全上書きのみ（部分編集禁止）

jarvis_core.agents.orchestrator をインポートしない（agents.py と agents/ の競合）

無料枠 API のみ使用（Gemini free tier, Semantic Scholar, PubMed）

ESM モジュール（import/export）を使用、path.join() で Windows パス処理

PowerShell here-string 内に JS の $ を書かない

npm install は npm ci または npm install --save で、余計な依存を増やさない

コミットメッセージは conventional-commit 形式（feat:, fix:, docs:, test: 等）

.env を絶対に git commit しない

Codex App の sandbox 内では spawn EPERM が出るため、テストは PowerShell 直接実行で確認

ファイル作成は notepad ファイル名 → 貼り付け → 保存 の手順（PowerShell の複雑なヒアドキュメントを避ける）

## 10. スモークテスト手順（セッション開始時に必ず実行）

Step 1: Git 状態確認

Copy
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline"

git status

git log --oneline -5

Step 2: Python バックエンド確認

Copy
.venv\Scripts\Activate.ps1

python --version      # → 3.11.9

python -m jarvis_cli --help   # → 22 コマンド表示

python -m pytest tests/ -q    # → 50 passed

Step 3: Agent-Web テスト

Copy
cd agent-web

npm test              # → 54 passed, 0 failed

（spawn EPERM の場合: node --test --test-isolation=none tests/*.test.js）

Step 4: サーバー起動

Copy
npm run dev           # → JARVIS Agent Web v1.0.0 running at http://localhost:3000

Step 5: ブラウザ確認

http://localhost:3000 を開く

Chat タブ: メッセージ送信→応答確認

Pipeline タブ: 進捗表示、results card、history 表示確認

Memory Panel: fact / preference / context の表示確認

Step 6: papers-repository 確認

Copy
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline"

node -e "import('./agent-web/src/db/papers-repository.js').then(m => { console.log('countPapers:', m.countPapers()); console.log('exports:', Object.keys(m)); }).catch(e => console.log('ERROR:', e.message))"

期待結果: countPapers: 0（または保存済み論文数）、9 関数のリスト

Step 7: タスクスケジューラ確認

Copy
schtasks /query /tn "JARVIS-DailyDigest"

期待結果: 次回実行 07:00、ステータス「準備完了」

## 11. Codex App 操作ガイド

エージェント定義

- explorer: read-only、コードベース調査・ファイル構造確認用
- worker: 実装用、ファイル作成・修正
- reviewer: コードレビュー、バグ発見、セキュリティチェック

並列実行パターン

- 独立した 3 タスクを 1 つのプロンプトに `=== TASK A ===` `=== TASK B ===` `=== TASK C ===` で記述
- Codex App に貼り付けて送信 → 3 タスク同時実行
- 全完了後にローカルで npm test → git add -A → git commit → git push
- 依存関係のあるタスクは前のバッチ完了後に次バッチを投入

注意事項

- server.js や index.html を複数タスクが同時変更すると競合する → 片方を先にコミット
- sandbox 内の spawn EPERM はコードの問題ではない
- worker の sandbox: workspace-write 設定で agent-web/ 配下のみ書き込み可能

## 12. 技術判断メモ

- ESM: agent-web 全体が ESM（import/export）。package.json に `"type": "module"` 設定済み
- dotenv: server.js 起動時に `../.env` を読み込み。CLI 実行時は `daily-digest.js` 内で `dotenv.config({ path: '../../.env' })`
- SSE パターン: pipeline.js / digest.js が Server-Sent Events で進捗送信。フロントは EventSource（GET のみ）
- better-sqlite3: 同期 API のため SQLITE_BUSY リスク低。WAL モード未設定
- Copilot API: copilot-api パッケージ（localhost:4141）経由で GitHub Copilot にアクセス。デフォルトモデル claude-sonnet-4.6
- フォールバックチェーン: Copilot API → Gemini API（LiteLLM 経由）
- PDF アーカイブ: Unpaywall API（doi ベース）→ 直接 URL → 失敗時スキップ

## 13. 主要パッケージバージョン

Node.js (agent-web)

- express: ^5.1.0
- better-sqlite3: ^11.10.0
- copilot-api: latest
- dotenv: ^16.6.1
- eventsource-parser: ^3.0.1
- js-yaml: ^4.1.1
- uuid: ^11.1.0
- nodemon: ^3.1.0 (dev)

Python

- jarvis-research-os==1.0.0
- google-genai==1.65.0
- litellm==1.82.0
- chromadb (latest)
- langgraph (latest)
- sentence-transformers (all-MiniLM-L6-v2)
- pyzotero, rapidfuzz, pydantic-ai, instructor
- streamlit==1.54.0
- pytest (latest)

## 14. 次セッションの推奨アクション

- CHAT-2: chat 内の PDF 表示と PDF 導線を追加
- PIPE-UI: pipeline results を progress bar + paper card + summary 表示へ拡張
- P3-6: LightRAG Web bridge を接続し、既知の asyncio.CancelledError を調査
- SEARCH-UI: advanced search UI with filters を設計
- DASH-1: digest / papers の analytics dashboard を追加

## 15. ファイル変更履歴（本セッション: 2026-03-06 Post-v16）

| ファイル | 操作 | 内容 |
|---|---|---|
| README.md | 修正 | Agent-Web Phase 3、Memory API、v2.0.0 ドキュメント更新 |
| agent-web/public/index.html | 修正 | Memory panel、responsive sidebar toggle、theme toggle、UI hook 追加 |
| agent-web/public/js/app.js | 修正 | Memory UI、responsive 動作、markdown 改善、reasoning trace、JSON highlight、DOI/PMID auto-link |
| agent-web/public/css/styles.css | 修正 | responsive layout、fade-in animations、theme variables、citation/trace/memory styles |
| agent-web/package.json | 修正 | `test:ci` に `tests/e2e.test.js` を追加 |
| agent-web/src/db/memory-store.js | 修正 | 空 preference 値の削除動作を追加し UI/E2E を補助 |
| agent-web/src/db/papers-repository.js | 修正 | `deletePaper` が numeric id / DOI の両方を受け付けるよう拡張 |
| agent-web/tests/e2e.test.js | 新規 | E2E 7 テストを追加（総数 54） |

この引き継ぎ書は 2026-03-06 06:00 JST 時点の状態を反映している。

---

## 次チャット開始時のコピペ用プロンプト

以下を次のチャットの最初のメッセージとしてそのまま貼り付けてください：

---

あなたは JARVIS Research OS + Agent-Web プロジェクトの開発を引き継ぐ AI エージェントです。

プロジェクト情報

GitHub: https://github.com/kaneko-ai/jarvis-ml-pipeline (main ブランチ)

引き継ぎ書: https://github.com/kaneko-ai/jarvis-ml-pipeline/blob/main/HANDOVER_v17.md

現在の状態（2026-03-06 06:00 JST 時点）

Python CLI v2.0.0: 22 コマンド、pytest 50/50 合格

Agent-Web: Express v5 + better-sqlite3、54/54 テスト合格、Memory UI、responsive layout、theme toggle、reasoning trace、JSON highlight + DOI/PMID auto-links 実装済み

Post-v16 セッション完了: MEM-1、README-1、UI-3、UI-4、UI-5、UI-6、THEME-1、CHAT-1、E2E-1

Phase 0〜3 全完了: Daily Digest（5キーワード×10件/日, Windows 07:00 自動実行）、papers CRUD、PDF アーカイバ、Zotero 同期、ChromaDB ブリッジ

環境

Windows 11, Node v24.13.1, Python 3.11.9

プロジェクト: C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline

ポート: 3000（Express）, 4141（Copilot API）

LLM: gemini-2.0-flash（デフォルト）, claude-sonnet-4.6（チャット）

.env に API キー設定済み（GEMINI_API_KEY, ZOTERO_API_KEY 等）

Codex App: explorer / worker / reviewer の 3 エージェント

最初にやること

HANDOVER_v17.md を読み込み、完全に理解する

セクション 10 のスモークテスト手順を提示する

セクション 6 の未実施タスクから、優先度の高いものを提案する

絶対ルール（セクション 9）と既知の問題（セクション 8）を確認し遵守する

絶対ルール（要約）

agent-web/ 外のファイルを変更しない（Web タスクの場合）

無料枠 API のみ使用

ESM + path.join で Windows パス処理

.env を git commit しない

conventional-commit 形式