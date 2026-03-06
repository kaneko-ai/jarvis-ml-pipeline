# HANDOVER_v19.md — JARVIS ML Pipeline 引き継ぎ書

> **Date**: 2026-03-06 22:30 JST
>
> **Authors**: Claude Opus 4.6 + kaneko yu
>
> **Previous**: HANDOVER_v18.md (2026-03-06 19:00 JST)
>
> **Audience**: AI (Claude / GPT / Codex)
>
> **GitHub**: https://github.com/kaneko-ai/jarvis-ml-pipeline (main)
>
> **関連リポジトリ**: https://github.com/kaneko-ai/zotero-doi-importer

---

## 0. Chain

v1 → v16 → v17 → v18 → v19

---

## 1. Overview

**JARVIS ML Pipeline** は 2 つのサブシステムで構成される AI 研究支援プラットフォームである。

### 1-A. Python CLI バックエンド (v2.0.0, tag: v2.0.0)

- 22 の CLI コマンド（search, pipeline, evidence, score, screen, browse, skills, mcp, orchestrate, obsidian-export, semantic-search, contradict, zotero-sync, pdf-extract, deep-research, citation-graph, citation, citation-stance, prisma, merge, note, run）
- PubMed / Semantic Scholar / OpenAlex / arXiv / Crossref から論文検索
- CEBM エビデンスグレーディング、ペーパースコアリング、矛盾検出
- ChromaDB ベクトル検索（~36 論文インデックス済み）
- LangGraph 6 エージェントオーケストレーター
- LiteLLM 統一 LLM アクセス（Gemini / OpenAI / DeepSeek）
- Obsidian ノート自動生成、Zotero 同期、PRISMA ダイアグラム、BibTeX 出力
- pytest **6944 passed** / **64 known failures**（agent-web とは無関係）

### 1-B. Agent-Web フロントエンド (Node.js/Express)

- Express v5 + better-sqlite3 + WebSocket（SSE も継続利用）
- Agent-Web テスト **80/80 pass**
- 単一ユーザー向けローカルツール（multi-user 前提は不要）
- 完了済み主要機能:
  - Memory UI
  - Dashboard
  - Chat Export
  - Notifications
  - Search UI
  - Responsive layout
  - Theme toggle
  - Reasoning trace
  - JSON highlight
  - DOI/PMID auto-links
  - PDF cards
  - Pipeline progress UI
  - PERF-1: Lazy-loaded tab modules（`app.js` → 8 modules）
  - AUTH-1: Token auth（デフォルト: `JARVIS_AUTH=disabled` for single user）
  - I18N-1: Japanese/English toggle
  - WS-1: WebSocket with auto-reconnect + status indicator
  - PWA-1: Service worker + offline cache + manifest
  - KEYBIND-1: Keyboard shortcuts（Ctrl+1-6 tabs, Ctrl+K chat, ? help）
  - IMPORT-1: BibTeX/RIS file import with drag-and-drop
- Daily Digest: 5 キーワード自動論文収集 → Gemini 要約 → SQLite 保存 → Obsidian 出力
- パイプライン: 7 ステップ SSE（検索→重複除去→スコアリング→ソート→Gemini 要約→JSON 生成→DB 保存+PDF アーカイブ）
- セッションメモリ（H-2）: 直近 20 メッセージをコンテキストとして送信
- 永続メモリ（H-3）: `facts` / `user_preferences` テーブルでクロスセッション記憶
- Memory API, export API, Dashboard analytics, Search UI, Auth, I18N, WebSocket, PWA, Keybinds, Import まで実装済み

---

## 2. Environment

| 項目 | 値 |
|---|---|
| OS | Windows 11 |
| Node.js | v24.13.1（confirmed） |
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
| .env | `JARVIS_AUTH=disabled`（single-user default） |

### .env ファイル（プロジェクトルート直下、1 ファイルのみ — .gitignore 済み）

Copy

ZOTERO_API_KEY=... ZOTERO_USER_ID=16956010 OPENAI_API_KEY=（空） DEEPSEEK_API_KEY=（空） LLM_MODEL=gemini/gemini-2.0-flash DATALAB_API_KEY=... GEMINI_API_KEY=... JARVIS_AUTH=disabled（実値は `.env` 参照）

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

---

## 3. Directory

```text
jarvis-ml-pipeline/
├── .env
├── .gitignore
├── config.yaml
├── README.md
├── HANDOVER_v16.md
├── HANDOVER_v17.md
├── HANDOVER_v18.md
├── HANDOVER_v19.md                   # ★ この文書
├── .github/
│   └── workflows/
│       └── test.yml
├── .codex/
│   └── agents/
│       ├── explorer.toml
│       ├── worker.toml
│       └── reviewer.toml
├── jarvis_cli/
├── jarvis_core/
├── jarvis_web/
├── tests/
└── agent-web/
    ├── package.json
    ├── data/
    │   ├── .gitignore
    │   ├── *.json
    │   └── digests/
    ├── public/
    │   ├── index.html
    │   ├── manifest.json
    │   ├── sw.js
    │   ├── icons/
    │   │   └── icon.svg
    │   ├── css/styles.css
    │   └── js/
    │       ├── app.js
    │       └── modules/
    │           ├── chat.js
    │           ├── pipeline.js
    │           ├── monitor.js
    │           ├── dashboard.js
    │           ├── memory.js
    │           ├── search.js
    │           ├── utils.js
    │           ├── i18n.js
    │           ├── ws-client.js
    │           └── keybinds.js
    ├── src/
    │   ├── server.js
    │   ├── middleware/
    │   │   └── auth.js
    │   ├── routes/
    │   │   ├── auth.js
    │   │   └── import.js
    │   ├── ws/
    │   │   └── websocket-manager.js
    │   ├── db/
    │   ├── skills/
    │   └── llm/
    └── tests/
        ├── api.test.js
        ├── auth.test.js
        ├── database.test.js
        ├── digest.test.js
        ├── i18n.test.js
        ├── pipeline.test.js
        ├── ws.test.js
        ├── pwa.test.js
        ├── keybinds.test.js
        └── import.test.js
```

新規/更新ファイル（v18→v19 で特に重要）:

- `agent-web/public/js/modules/chat.js`
- `agent-web/public/js/modules/pipeline.js`
- `agent-web/public/js/modules/monitor.js`
- `agent-web/public/js/modules/dashboard.js`
- `agent-web/public/js/modules/memory.js`
- `agent-web/public/js/modules/search.js`
- `agent-web/public/js/modules/utils.js`
- `agent-web/public/js/modules/i18n.js`
- `agent-web/public/js/modules/ws-client.js`
- `agent-web/public/js/modules/keybinds.js`
- `agent-web/src/middleware/auth.js`
- `agent-web/src/routes/auth.js`
- `agent-web/src/routes/import.js`
- `agent-web/src/ws/websocket-manager.js`
- `agent-web/public/manifest.json`
- `agent-web/public/sw.js`
- `agent-web/public/icons/icon.svg`
- `agent-web/tests/auth.test.js`
- `agent-web/tests/i18n.test.js`
- `agent-web/tests/ws.test.js`
- `agent-web/tests/pwa.test.js`
- `agent-web/tests/keybinds.test.js`
- `agent-web/tests/import.test.js`
- `agent-web/data/.gitignore`
- `HANDOVER_v19.md`

---

## 4. API

| メソッド | パス | 説明 | 状態 |
|---|---|---|---|
| POST | /api/chat/stream | チャット（SSE + メモリ統合） | ✅ |
| GET | /api/sessions | セッション一覧 | ✅ |
| GET | /api/sessions/:id/export | チャット履歴 Markdown export | ✅ |
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
| POST | /api/auth/login | authenticate with token | ✅ |
| GET | /api/auth/status | check auth status | ✅ |
| POST | /api/auth/logout | clear session | ✅ |
| POST | /api/import/bibtex | import papers from BibTeX text | ✅ |
| POST | /api/import/ris | import papers from RIS text | ✅ |
| GET | /api/health | 簡易ヘルス | ✅ |
| WS | /ws | WebSocket real-time communication | ✅ |
| — | /data/* | 静的 JSON 配信 | ✅ |

---

## 5. Completed Phases

Phase 0: 環境構築 ✅

- Codex App 3 エージェント定義、config 修正、Git safe.directory、better-sqlite3、paper-search.js 動作確認、.har 除去

Phase 1: コア機能 ✅

- 3 タブ UI、parallel-runner.js、pipeline.js（SSE 7 ステップ）、monitor.js、Gemini 要約、エラーハンドリング

Phase 2: Daily Digest ✅

- P2-1: Daily Digest 初回実行テスト成功（5 キーワード, 49 論文, 2026-03-05）
- P2-2: Windows タスクスケジューラ登録済み（毎日 07:00, `JARVIS-DailyDigest`）
- P2-3: Digest→Obsidian 自動出力（digest-to-obsidian.js）

Phase 3: データ管理 ✅

- P3-1: SQLite papers テーブル + CRUD
- P3-2: 重複排除強化
- P3-3: PDF アーカイバ
- P3-4: Zotero 同期
- P3-5: ChromaDB ブリッジ
- パイプライン→DB 保存 / PDF アーカイブ / Digest→Obsidian 自動出力

品質改善 ✅

- Gemini レートリミット対策
- API 429 リトライ
- パイプライン DB 保存
- GEMINI_API_KEY 未設定ガード

H-2: セッションメモリ ✅

- 直近 20 メッセージをコンテキスト送信
- 研究論文コンテキストをシステムプロンプトに注入

H-3: 永続クロスセッションメモリ ✅

- facts テーブル + user_preferences テーブル
- メモリコンテキスト生成 / ファクト抽出保存

Memory API ✅

- `/api/memory/*` エンドポイント群
- server.js 登録済み

Session 2026-03-06 Morning (v16→v17) ✅

- MEM-1
- README-1
- UI-3
- UI-4
- UI-5
- E2E-1

Session 2026-03-06 Afternoon (v17→v18) ✅

- UI-6: Reasoning trace display
- THEME-1: Light/dark theme toggle with CSS custom properties
- CHAT-1: JSON syntax highlight, DOI/PMID auto-links
- CHAT-2: PDF card display, Unpaywall lookup
- PIPE-UI: Pipeline progress bar, paper cards, summary display
- DASH-1: Dashboard analytics (stats, digest timeline, health)
- EXPORT-1: Chat history Markdown export + download
- NOTIF-1: Browser notifications + toast system
- SEARCH-UI: Advanced search panel with filters
- TEST-FIX: api.test.js server-independent

Session 2026-03-06 Evening (v18→v19) ✅

- PERF-1: `app.js` split into 8 lazy-loaded modules
- AUTH-1: Token auth（disabled by default for single-user）
- I18N-1: Japanese/English i18n with `data-i18n` + `localStorage`
- WS-1: WebSocket server + browser client with auto-reconnect
- PWA-1: Service worker, `manifest.json`, offline cache
- KEYBIND-1: 12 keyboard shortcuts with help overlay（Shift+?）
- IMPORT-1: BibTeX/RIS parser + drag-and-drop import UI

テスト状況 ✅

- agent-web: **80/80 pass**（2026-03-06 22:30 JST 時点）
- Python: 6944 passed / 64 known failures（agent-web 無関係）

---

## 6. Remaining Tasks

高優先度 🔴

- （なし）

中優先度 🟡

| ID | タスク | 備考 |
|---|---|---|
| P3-6 | LightRAG Web bridge | `asyncio.CancelledError` unresolved |
| WS-MIGRATE | Migrate SSE endpoints to WebSocket fully | SSE 互換は現状維持 |

低優先度 🟢

| ID | タスク | 備考 |
|---|---|---|
| RC-1 | Remote control API | 外部制御用 API |
| PLUGIN-1 | Plugin system for custom skills | custom skills 拡張 |
| OFFLINE-1 | Full offline mode | PWA foundation ready |

新規アイデア 💡

- CHART-1: Interactive charts（D3.js / Chart.js）for dashboard
- ANNOTATE-1: Paper annotation and highlighting
- TAG-1: Custom paper tagging and filtering
- BACKUP-1: One-click DB export/import for backup
- TEMPLATE-1: Custom research note templates

---

## 7. Git History

2026-03-06 の主要コミット:

- `9a89923f` feat: pipeline PDF archive + digest Obsidian export, 39 tests, HANDOVER_v15
- `77ee9826` feat: H-2 session memory, H-3 persistent memory, UI Phase 2 text animations
- `d0b529b5` docs: HANDOVER_v16.md – full project handover (Phase 0-3 complete, 47 tests, memory API)
- `880f85df` docs: update README.md with Agent-Web Phase 3, Memory API, v2.0.0
- `bf0a9155` feat(agent-web): add Memory management UI panel (MEM-1)
- `2b964cbb` temporary / placeholder commit (`-`)
- `e3ab473a` feat(agent-web): responsive layout, fade-in animations, E2E tests (UI-3, UI-5, E2E-1)
- `7cbdb627` feat(agent-web): reasoning trace, light/dark theme toggle, JSON highlight + DOI/PMID links (UI-6, THEME-1, CHAT-1)
- `38636d79` feat(agent-web): PDF card display, Unpaywall lookup link, PDF badge in chat (CHAT-2)
- `cce277fd` feat(agent-web): pipeline progress bar, paper cards, summary display (PIPE-UI)
- `d6cb5633` docs: HANDOVER_v17.md – session 2026-03-06 (MEM-1, UI-3~6, THEME-1, CHAT-1, E2E-1, 54 tests)
- `57fa9dbe` feat(agent-web): PDF cards, pipeline progress UI, HANDOVER_v17 (CHAT-2, PIPE-UI) - 54 tests
- `5456f62a` chore: remove worktrees/ temp files and add to .gitignore
- `a75c19a2` feat(agent-web): add Dashboard analytics view with stats and digest timeline (DASH-1)
- `6cfb4146` feat(agent-web): chat history Markdown export with download (EXPORT-1)
- `81b06837` feat(agent-web): browser notifications and toast system for digest/pipeline events (NOTIF-1)
- `408f8f1a` feat(agent-web): advanced search panel with source/year filters (SEARCH-UI)
- `b7f9290f` fix(agent-web): make api.test.js server-independent with in-process test server (TEST-FIX)
- `a06ca147` docs: HANDOVER_v18.md – full session 2026-03-06 (15 tasks, 55 tests)
- `0ad8ef79` feat(agent-web): lazy-load tabs, add token auth, and add Japanese/English i18n
- `71d6ef5a` feat(agent-web): WebSocket support with auto-reconnect client and status indicator (WS-1)
- `086a1bf6` feat(agent-web): PWA support with service worker, manifest, and offline cache (PWA-1)
- `34a2088e` docs: HANDOVER_v19.md – evening session 2026-03-06 (PERF+AUTH+I18N+WS+PWA, 71+ tests)
- `20cb1edf` feat(agent-web): keyboard shortcuts with help overlay (KEYBIND-1)
- `aea9e191` feat(agent-web): BibTeX/RIS file import with drag-and-drop (IMPORT-1)
- `(pending)` docs: HANDOVER_v19.md – evening session (PERF+AUTH+I18N+WS+PWA+KEYBIND+IMPORT)

---

## 8. Known Issues

| 問題 | 深刻度 | 対処法 |
|---|---|---|
| npm test で spawn EPERM | 低 | Codex App サンドボックス内でのみ発生。`node --test --test-isolation=none tests/*.test.js` を使用 |
| OPENAI_API_KEY が空 | 低 | OpenAI 系機能は動作しない。gemini-2.0-flash で代替 |
| DEEPSEEK_API_KEY が空 | 低 | DeepSeek フォールバック不可 |
| claude-opus-4.6 で 400 エラー | 中 | claude-sonnet-4.6 を使用 |
| gpt-5.1 で 400 エラー | 中 | gpt-4.1 を使用 |
| Gemini レートリミット | 中 | concurrency 1, delay 4500ms で対策済み |
| Semantic Scholar レートリミット | 中 | 1500ms 遅延 + 429 リトライ |
| PubMed レートリミット | 低 | 350ms 遅延で対策済み |
| LightRAG asyncio.CancelledError | 中 | P3-6 で対応予定 |
| Datalab API 403 | 低 | PyMuPDF にフォールバック |
| H: ドライブ切断 | 低 | Google Drive 再接続で復旧 |
| agents.py vs agents/ 競合 | 低 | `jarvis_core.agents.orchestrator` を import しない |
| Scrapling css_first 未定義 | 低 | browse.py 利用時に注意 |
| PowerShell で $1 消失 | 中 | here-string ではなく別ファイル経由で回避 |
| LF/CRLF 警告 | 低 | 動作影響なし |
| config.yaml Zotero api_key 空 | 低 | `.env` の ZOTERO_API_KEY とは別管理 |
| git-credential-manager rename warning | 低 | cosmetic only |
| Python pytest 64 failures | 中 | `ContradictionDetector` signature, MCP Hub, ChromaDB `google.rpc` 系。agent-web とは無関係 |
| Codex worktrees / temp files | 低 | `.gitignore` 追加済みだが一時ファイル残骸に注意 |
| Service worker cache | 低 | 変更後は `CACHE_NAME` version を bump する |
| Auth token in plaintext | 低 | ローカル single-user 用としては許容、production では不可 |
| WebSocket reconnect | 低 | ページリロード時に brief red dot が表示されることがある |

---

## 9. Absolute Rules

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

---

## 10. Smoke Test

Step 1: Git 状態確認

Copy
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline"

git status

git log --oneline -5

Step 2: Python バックエンド確認

Copy
.venv\Scripts\Activate.ps1

python --version

python -m jarvis_cli --help

python -m pytest tests/ -q

Step 3: Agent-Web テスト

Copy
cd agent-web

npm test

（spawn EPERM の場合: `node --test --test-isolation=none tests/*.test.js`）

期待結果: **80 passed, 0 failed**

Step 4: サーバー起動

Copy
npm run dev

期待結果: `JARVIS Agent Web v1.0.0 running on http://localhost:3000`

Step 5: ブラウザ確認

- `http://localhost:3000` を開く
- Chat タブ: メッセージ送信→応答確認
- Pipeline タブ: 進捗表示、paper cards、history 表示確認
- Dashboard タブ: stats / digest timeline / health が表示されること
- Memory タブ: fact / preference / context の表示確認
- Theme toggle: light/dark が切り替わること
- Verify language toggle（EN/JA）
- Check WebSocket green dot in sidebar
- Press Shift+? to verify shortcuts help overlay
- Drag a `.bib` file onto Pipeline tab to test import

Step 6: papers-repository 確認

Copy
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline"

node -e "import('./agent-web/src/db/papers-repository.js').then(m => { console.log('countPapers:', m.countPapers()); console.log('exports:', Object.keys(m)); }).catch(e => console.log('ERROR:', e.message))"

Step 7: タスクスケジューラ確認

Copy
schtasks /query /tn "JARVIS-DailyDigest"

---

## 11. Codex App Notes

エージェント定義

- explorer: read-only、コードベース調査・ファイル構造確認用
- worker: 実装用、ファイル作成・修正
- reviewer: コードレビュー、バグ発見、セキュリティチェック

並列実行パターン

- 独立した 3 タスクを 1 つのプロンプトに `=== TASK A ===` `=== TASK B ===` `=== TASK C ===` で記述
- Codex App に貼り付けて送信 → 3 タスク同時実行
- 全完了後にローカルで `npm test` → `git add -A` → `git commit` → `git push`
- 依存関係のあるタスクは前のバッチ完了後に次バッチを投入

注意事項

- `server.js` や `index.html` を複数タスクが同時変更すると競合する → 片方を先にコミット
- sandbox 内の spawn EPERM はコードの問題ではない
- worker の sandbox は `workspace-write`、基本は `agent-web/` 配下のみ書き込み可能

---

## 12. Architecture Notes

- ESM: agent-web 全体が ESM（import/export）。`package.json` に `"type": "module"` 設定済み
- dotenv: `server.js` 起動時に `../.env` を読み込み。CLI 実行時は各スクリプト内で個別に `dotenv.config()`
- SSE パターン: `pipeline.js` / `digest.js` が Server-Sent Events で進捗送信。フロントは EventSource / fetch stream の併用
- better-sqlite3: 同期 API のため SQLITE_BUSY リスク低。WAL モード有効
- Copilot API: `copilot-api`（localhost:4141）経由で GitHub Copilot にアクセス
- フォールバックチェーン: Copilot API → Gemini API（LiteLLM 経由）
- PDF アーカイブ: Unpaywall API（doi ベース）→ 直接 URL → 失敗時スキップ
- Toast notification system: `showToast()` + `showNotification()`
- Theme: CSS custom properties + `data-theme` attribute + `localStorage`
- Export: `/api/sessions/:id/export` は `Content-Disposition` 付き download を返す
- Module system: `app.js` は thin orchestrator、タブの実装は `modules/*.js` に分離
- Auth: `JARVIS_AUTH=disabled` が single-user のデフォルト
- Keybinds: `keybinds.js` が document `keydown` を監視し、入力中は非 Ctrl ショートカットを無視
- Import: BibTeX regex parser + RIS tag-based parser を server-side で処理
- WebSocket: `ws` package、heartbeat 30s、client-side auto-reconnect 3s
- PWA: static は stale-while-revalidate、`/api/` は network-only

---

## 13. Dependencies

Node.js (agent-web)

- express: ^5.1.0
- better-sqlite3: ^11.10.0
- copilot-api: latest
- dotenv: ^16.6.1
- eventsource-parser: ^3.0.1
- js-yaml: ^4.1.1
- uuid: ^11.1.0
- ws: ^8.18.0
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

---

## 14. Next Actions

1. CHART-1: Interactive dashboard charts
2. TAG-1: Paper tagging system
3. BACKUP-1: DB export/import

---

## 15. Changed Files

2026-03-06（v18→v19）で変更された主要ファイル:

- `HANDOVER_v19.md`
- `agent-web/package-lock.json`
- `agent-web/package.json`
- `agent-web/public/css/styles.css`
- `agent-web/public/icons/icon.svg`
- `agent-web/public/index.html`
- `agent-web/public/js/app.js`
- `agent-web/public/js/modules/chat.js`
- `agent-web/public/js/modules/dashboard.js`
- `agent-web/public/js/modules/i18n.js`
- `agent-web/public/js/modules/keybinds.js`
- `agent-web/public/js/modules/memory.js`
- `agent-web/public/js/modules/monitor.js`
- `agent-web/public/js/modules/pipeline.js`
- `agent-web/public/js/modules/search.js`
- `agent-web/public/js/modules/utils.js`
- `agent-web/public/js/modules/ws-client.js`
- `agent-web/public/manifest.json`
- `agent-web/public/sw.js`
- `agent-web/src/middleware/auth.js`
- `agent-web/src/routes/auth.js`
- `agent-web/src/routes/import.js`
- `agent-web/src/server.js`
- `agent-web/src/ws/websocket-manager.js`
- `agent-web/tests/auth.test.js`
- `agent-web/tests/i18n.test.js`
- `agent-web/tests/import.test.js`
- `agent-web/tests/keybinds.test.js`
- `agent-web/tests/pwa.test.js`
- `agent-web/tests/ws.test.js`

この引き継ぎ書は 2026-03-06 22:30 JST 時点の状態を反映している。

---

## 次チャット開始時のコピペ用プロンプト

以下を次のチャットの最初のメッセージとしてそのまま貼り付けてください：

---

あなたは JARVIS Research OS + Agent-Web プロジェクトの開発を引き継ぐ AI エージェントです。

プロジェクト情報

GitHub: https://github.com/kaneko-ai/jarvis-ml-pipeline (main ブランチ)

引き継ぎ書: https://github.com/kaneko-ai/jarvis-ml-pipeline/blob/main/HANDOVER_v19.md

現在の状態（2026-03-06 22:30 JST 時点）

Python CLI v2.0.0: 22 コマンド、pytest 6944 passed / 64 known failures（agent-web とは無関係）

Agent-Web: Express v5 + better-sqlite3 + WebSocket、80/80 テスト合格、single-user local tool

2026-03-06 追加完了: PERF-1、AUTH-1、I18N-1、WS-1、PWA-1、KEYBIND-1、IMPORT-1

既存完了: Dashboard、Export、Notifications、Search UI、Memory UI、responsive layout、theme toggle、reasoning trace、JSON highlight、DOI/PMID auto-links、PDF cards、pipeline progress UI

環境

Windows 11, Node v24.13.1, Python 3.11.9

プロジェクト: C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline

ポート: 3000（Express）, 4141（Copilot API）

LLM: gemini-2.0-flash（デフォルト）, claude-sonnet-4.6（チャット）

.env に API キー設定済み（GEMINI_API_KEY, ZOTERO_API_KEY 等）+ `JARVIS_AUTH=disabled`

Codex App: explorer / worker / reviewer の 3 エージェント

最初にやること

HANDOVER_v19.md を読み込み、完全に理解する

セクション 10 のスモークテスト手順を提示する

セクション 6 の未実施タスクから、優先度の高いものを提案する

絶対ルール（セクション 9）と既知の問題（セクション 8）を確認し遵守する

絶対ルール（要約）

agent-web/ 外のファイルを変更しない（Web タスクの場合）

無料枠 API のみ使用

ESM + path.join で Windows パス処理

.env を git commit しない

conventional-commit 形式
