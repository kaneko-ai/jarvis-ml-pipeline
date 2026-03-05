\# HANDOVER\_v16.md — JARVIS ML Pipeline 引き継ぎ書



> \*\*作成日\*\*: 2026-03-06 01:00 JST

> \*\*作成者\*\*: Claude Opus 4.6 + kaneko yu

> \*\*前回引き継ぎ\*\*: HANDOVER\_v15.md (2026-03-05 23:30 JST)

> \*\*対象\*\*: 次チャットの AI エージェント（Claude / GPT / Codex 等）

> \*\*GitHub\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline (main ブランチ)

> \*\*関連リポジトリ\*\*: https://github.com/kaneko-ai/zotero-doi-importer



---



\## 0. この文書の読み方



この引き継ぎ書 1 枚でプロジェクトの「環境・構成・完了済み作業・未完了タスク・既知の問題・絶対ルール」をすべて把握できる。過去の HANDOVER\_v1〜v15 を読む必要はない。



---



\## 1. プロジェクト概要



\*\*JARVIS ML Pipeline\*\* は 2 つのサブシステムで構成される AI 研究支援プラットフォームである。



\### 1-A. Python CLI バックエンド (v2.0.0, tag: v2.0.0)

\- 22 の CLI コマンド（search, pipeline, evidence, score, screen, browse, skills, mcp, orchestrate, obsidian-export, semantic-search, contradict, zotero-sync, pdf-extract, deep-research, citation-graph, citation, citation-stance, prisma, merge, note, run）

\- PubMed / Semantic Scholar / OpenAlex / arXiv / Crossref から論文検索

\- CEBM エビデンスグレーディング、ペーパースコアリング、矛盾検出

\- ChromaDB ベクトル検索（~36 論文インデックス済み）

\- LangGraph 6 エージェントオーケストレーター

\- LiteLLM 統一 LLM アクセス（Gemini / OpenAI / DeepSeek）

\- Obsidian ノート自動生成、Zotero 同期、PRISMA ダイアグラム、BibTeX 出力

\- pytest 50 テスト全パス



\### 1-B. Agent-Web フロントエンド (Node.js/Express)

\- Express v5 + better-sqlite3 + SSE ストリーミング

\- 3 タブ UI（Chat | Pipeline | Monitor）+ ダーク/ゴールドテーマ

\- Daily Digest: 5 キーワード自動論文収集 → Gemini 要約 → SQLite 保存 → Obsidian 出力

\- パイプライン: 7 ステップ SSE（検索→重複除去→スコアリング→ソート→Gemini 要約→JSON 生成→DB 保存+PDF アーカイブ）

\- セッションメモリ（H-2）: 直近 20 メッセージをコンテキストとして送信

\- 永続メモリ（H-3）: facts / user\_preferences テーブルでクロスセッション記憶

\- Memory API: /api/memory/\* エンドポイント（facts CRUD, preferences, context）

\- テスト: \*\*47 テスト全パス\*\*（2026-03-06 00:56 JST 最終確認）



---



\## 2. 環境情報（2026-03-06 時点で動作確認済み）



| 項目 | 値 |

|---|---|

| OS | Windows 11 |

| Node.js | v24.13.1 |

| npm | 11.8.0 |

| Python | 3.11.9（.venv）/ 3.12.3（venv、旧） |

| Git | 設定済み（safe.directory 登録済み） |

| プロジェクトルート | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| agent-web ルート | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web` |

| Python venv | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\.venv` |

| Obsidian Vault | `H:\\obsidian-vault`（config.yaml: `H:\\\\obsidian-vault`） |

| データ保存先 | `H:\\jarvis-data\\`（logs, exports, pdf-archive, digests） |

| GitHub | `https://github.com/kaneko-ai/jarvis-ml-pipeline.git` (main) |

| ポート | 3000（Express）, 4141（Copilot API）, 8501（Streamlit, 待機） |

| LLM | gemini-2.0-flash（デフォルト）, claude-sonnet-4.6（チャット）, gpt-4.1, o4-mini |

| Codex App | 3 エージェント（explorer, worker, reviewer）定義済み |

| C: ドライブ空き | ~45 GB |

| H: ドライブ | Google Drive 2 TB（使用 57 GB） |



\### .env ファイル（プロジェクトルート直下、1 ファイルのみ — .gitignore 済み）



Copy

ZOTERO\_API\_KEY=wc3GxeCPThtkWJnvVJQsLtLb ZOTERO\_USER\_ID=16956010 OPENAI\_API\_KEY=（空） DEEPSEEK\_API\_KEY=（空） LLM\_MODEL=gemini/gemini-2.0-flash DATALAB\_API\_KEY=ng2yRJcuRfpvc0mCRwENWwGucyfLq5eTOXMTBB7eeyY GEMINI\_API\_KEY=AIzaSyCK...（実値は .env 参照）





\### config.yaml（プロジェクトルート直下）



```yaml

obsidian:

&nbsp; vault\_path: "H:\\\\obsidian-vault"

&nbsp; papers\_folder: JARVIS/Papers

&nbsp; notes\_folder: JARVIS/Notes

zotero:

&nbsp; api\_key: ''

&nbsp; user\_id: ''

&nbsp; collection: JARVIS

search:

&nbsp; default\_sources: \[pubmed, semantic\_scholar, openalex]

&nbsp; max\_results: 20

llm:

&nbsp; default\_provider: gemini

&nbsp; default\_model: gemini/gemini-2.0-flash

&nbsp; fallback\_model: openai/gpt-4.1

&nbsp; models:

&nbsp;   gemini: gemini/gemini-2.0-flash

&nbsp;   openai: openai/gpt-5-mini

&nbsp;   deepseek: deepseek/deepseek-reasoner

&nbsp; cache\_enabled: true

&nbsp; max\_retries: 3

&nbsp; temperature: 0.3

evidence:

&nbsp; use\_llm: false

&nbsp; strategy: weighted\_average

storage:

&nbsp; logs\_dir: "H:\\\\jarvis-data\\\\logs"

&nbsp; exports\_dir: "H:\\\\jarvis-data\\\\exports"

&nbsp; pdf\_archive\_dir: "H:\\\\jarvis-data\\\\pdf-archive"

&nbsp; local\_fallback: logs

digest:

&nbsp; keywords:

&nbsp;   - "CRISPR gene therapy"

&nbsp;   - "PD-1 immunotherapy"

&nbsp;   - "PD-1"

&nbsp;   - "spermidine"

&nbsp;   - "cancer"

&nbsp; schedule\_hour: 7

&nbsp; schedule\_minute: 0

&nbsp; papers\_per\_keyword: 10

&nbsp; summarize\_top\_n: 5

&nbsp; output\_dir: "agent-web/data/digests"

3\. ディレクトリ構成（主要部分）

jarvis-ml-pipeline/

├── .env                              # API キー（GEMINI\_API\_KEY 等）

├── .gitignore

├── config.yaml                       # 全体設定

├── run-daily-digest.bat              # タスクスケジューラ用バッチ

├── HANDOVER\_v16.md                   # ★ この文書

├── HANDOVER\_v15.md

├── HANDOVER\_v14.md

├── JARVIS\_EXPANSION\_PLAN\_v1.md

├── .github/

│   └── workflows/

│       └── test.yml                  # CI/CD（GitHub Actions）

├── .codex/

│   └── agents/

│       ├── explorer.toml

│       ├── worker.toml

│       └── reviewer.toml

├── jarvis\_cli/                       # Python CLI（22 コマンド）

├── jarvis\_core/                      # Python コアライブラリ

│   ├── embeddings/                   # ChromaDB PaperStore

│   ├── evidence.py                   # CEBM エビデンスグレーディング

│   ├── llm/                          # LiteLLM クライアント

│   ├── mcp/                          # MCP Hub（5 サーバー, 15 ツール）

│   ├── pdf/                          # PDF→Markdown

│   ├── rag/                          # LightRAG, CitationGraph

│   ├── sources/                      # 統合論文検索

│   └── storage\_utils.py              # H: ドライブ / ローカルフォールバック

├── jarvis\_web/                       # Streamlit ダッシュボード

├── tests/                            # pytest（50 テスト）

├── scripts/                          # Python ユーティリティ（80+ ファイル）

├── .chroma/                          # ChromaDB 永続データ（~36 論文）

├── .lightrag/                        # LightRAG データ

└── agent-web/                        # ★ Node.js Web アプリ

&nbsp;   ├── package.json                  # ESM, "test": "node --test tests/\*.test.js"

&nbsp;   ├── data/

&nbsp;   │   ├── \*.json                    # パイプライン結果

&nbsp;   │   └── digests/                  # Daily Digest 出力

&nbsp;   │       ├── digest-2026-03-05.json (4977 B)

&nbsp;   │       ├── digest-2026-03-05.md   (3611 B)

&nbsp;   │       ├── digest-2026-03-06.json (4459 B)

&nbsp;   │       └── digest-2026-03-06.md   (3027 B)

&nbsp;   ├── public/

&nbsp;   │   ├── index.html                # 3 タブ SPA

&nbsp;   │   ├── css/styles.css            # ダーク/ゴールドテーマ + アニメーション

&nbsp;   │   └── js/app.js                 # フロントエンド（652+ 行）

&nbsp;   ├── src/

&nbsp;   │   ├── server.js                 # Express v5 エントリポイント

&nbsp;   │   ├── db/

&nbsp;   │   │   ├── database.js           # sessions + messages テーブル

&nbsp;   │   │   ├── jarvis.db             # SQLite DB ファイル

&nbsp;   │   │   ├── papers-repository.js  # papers CRUD（9 関数）

&nbsp;   │   │   ├── memory-store.js       # facts + user\_preferences（H-3）

&nbsp;   │   │   ├── chroma-bridge.js      # Python ChromaDB 連携

&nbsp;   │   │   └── create-papers-table.js # マイグレーションスクリプト

&nbsp;   │   ├── llm/

&nbsp;   │   │   ├── paper-search.js       # PubMed + S2 + OpenAlex（429 リトライ付き）

&nbsp;   │   │   ├── gemini-summarizer.js  # Gemini 2.0 Flash（concurrency:1, delay:4500ms）

&nbsp;   │   │   ├── parallel-runner.js    # プール管理（api:4, gemini:3, copilot:1）

&nbsp;   │   │   ├── copilot-bridge.js

&nbsp;   │   │   ├── jarvis-tools.js

&nbsp;   │   │   └── python-bridge.js

&nbsp;   │   ├── routes/

&nbsp;   │   │   ├── chat.js               # /api/chat/stream（SSE）+ メモリ統合

&nbsp;   │   │   ├── pipeline.js           # 7 ステップ SSE + DB 保存 + PDF アーカイブ

&nbsp;   │   │   ├── digest.js             # /api/digest/run, /history, /report/:filename

&nbsp;   │   │   ├── monitor.js            # /status, /health, /history

&nbsp;   │   │   ├── memory.js             # /api/memory/\* (facts, preferences, context)

&nbsp;   │   │   ├── sessions.js

&nbsp;   │   │   ├── models.js

&nbsp;   │   │   ├── skills.js

&nbsp;   │   │   ├── mcp.js

&nbsp;   │   │   └── usage.js

&nbsp;   │   ├── skills/

&nbsp;   │   │   ├── daily-digest.js       # Daily Digest + Obsidian 自動出力

&nbsp;   │   │   ├── digest-to-obsidian.js # Obsidian vault へ MD エクスポート

&nbsp;   │   │   ├── pdf-archiver.js       # PDF ダウンロード + アーカイブ

&nbsp;   │   │   ├── zotero-sync.js        # Zotero Web API v3 同期

&nbsp;   │   │   └── skill-registry.js

&nbsp;   │   ├── middleware/

&nbsp;   │   └── mcp-bridge/

&nbsp;   └── tests/

&nbsp;       ├── database.test.js          # 5 テスト

&nbsp;       ├── api.test.js               # 5 テスト（サーバー起動必要）

&nbsp;       ├── digest.test.js            # 19 テスト（memory-store, chat 含む）

&nbsp;       ├── pipeline.test.js          # 2 テスト

&nbsp;       ├── monitor.test.js           # 2 テスト

&nbsp;       ├── gemini-summarizer.test.js # 3 テスト

&nbsp;       └── parallel-runner.test.js   # 4 テスト

&nbsp;       （api.test.js 除外で 42 テスト、全込み 47 テスト）

4\. API エンドポイント一覧

メソッド	パス	説明	状態

POST	/api/chat/stream	チャット（SSE + メモリ統合）	✅

GET	/api/sessions	セッション一覧	✅

GET	/api/models	LLM モデル一覧	✅

GET	/api/skills	スキル一覧	✅

GET/POST	/api/mcp/\*	MCP ブリッジ	✅

GET	/api/usage	使用量	✅

GET	/api/pipeline/run?query=…\&limit=…	パイプライン実行（SSE 7 ステップ）	✅

GET	/api/pipeline/history	パイプライン履歴	✅

GET/POST	/api/digest/run	Daily Digest 実行（SSE）	✅

GET	/api/digest/history	Digest 履歴	✅

GET	/api/digest/report/:filename	Digest レポート取得	✅

GET	/api/monitor/status	システム状態	✅

GET	/api/monitor/health	ヘルスチェック	✅

GET	/api/monitor/history	Monitor 履歴	✅

GET	/api/memory/facts	全 facts 取得	✅

GET	/api/memory/facts/:key	単一 fact 取得	✅

POST	/api/memory/facts	fact 保存	✅

DELETE	/api/memory/facts/:key	fact 削除	✅

GET	/api/memory/preferences	全 preferences 取得	✅

POST	/api/memory/preferences	preference 保存	✅

GET	/api/memory/context	メモリコンテキスト取得	✅

GET	/api/health	簡易ヘルス	✅

—	/data/\*	静的 JSON 配信	✅

5\. 完了済み全タスク

Phase 0: 環境構築 ✅

Codex App 3 エージェント定義、config 修正、Git safe.directory、better-sqlite3、paper-search.js 動作確認、.har 除去

Phase 1: コア機能 ✅

3 タブ UI、parallel-runner.js、pipeline.js（SSE 7 ステップ）、monitor.js、Gemini 要約、エラーハンドリング、21 テスト全パス

Phase 2: Daily Digest ✅

P2-1: Daily Digest 初回実行テスト成功（5 キーワード, 49 論文, 2026-03-05）

P2-2: Windows タスクスケジューラ登録済み（毎日 07:00, 「JARVIS-DailyDigest」タスク確認済み）

P2-3: Digest→Obsidian 自動出力（digest-to-obsidian.js）

Phase 3: データ管理 ✅

P3-1: SQLite papers テーブル + CRUD（papers-repository.js, 9 関数: init, insertPaper, insertPapers, getPapers, getPaperByDoi, getPaperByPmid, searchPapers, countPapers, deletePaper）

P3-2: 重複排除強化（titleSimilarity in pipeline.js）

P3-3: PDF アーカイバ（pdf-archiver.js — Unpaywall + 直接ダウンロード）

P3-4: Zotero 同期（zotero-sync.js — Zotero Web API v3）

P3-5: ChromaDB ブリッジ（chroma-bridge.js — Python subprocess）

パイプライン→DB 自動保存（pipeline.js 内で insertPapers 実行）

パイプライン→PDF アーカイブ（best-effort, 失敗時は警告のみ）

Daily Digest→Obsidian 自動出力（best-effort）

品質改善 ✅

Gemini レートリミット対策: concurrency 1, delay 4500ms（15 RPM 以内で安全）

API 429 リトライ: PubMed 350ms 遅延 + リトライ、S2 1500ms + 5 秒待ちリトライ（最大 2 回）

パイプライン DB 保存: papers テーブルへ自動 INSERT

GEMINI\_API\_KEY 未設定ガード（summarizeBatch 内）

H-2: セッションメモリ ✅

chat.js に SYSTEM\_PROMPT 定義、メッセージ順序 \[system, …history, user] 統一

直近 20 メッセージをコンテキスト送信（buildHistory()）

SQLite papers テーブルから研究キーワードに関連する上位 3 件を検索し、システムプロンプトに注入

H-3: 永続クロスセッションメモリ ✅

memory-store.js: facts テーブル + user\_preferences テーブル

エクスポート関数: storeFact, getFact, getFactsByCategory, getAllFacts, deleteFact, setPreference, getPreference, getAllPreferences, getMemoryContext, extractAndStoreFacts

chat.js 統合: getMemoryContext() でユーザー記憶をプロンプトに注入、extractAndStoreFacts() で応答からファクト抽出

Memory API ✅

memory.js ルート: /api/memory/\* エンドポイント 7 つ

server.js に memoryRouter 登録済み

UI Phase 1 ✅

ダーク/ゴールドテーマ、パーティクル背景、フロストガラスサイドバー、星ロゴ、コードブロック highlight+copy

UI Phase 2（部分完了）✅

text-reveal アニメーション（300ms フェード+ブラー）

activity-dot ステータス（running=パルス, done=✓緑, error=✗赤）

コードブロック slideInLeft アニメーション

CI/CD ✅

.github/workflows/test.yml（Node.js 24, npm ci, npm run test:ci）

package.json に test:ci スクリプト追加（api.test.js 除外）

テスト状況 ✅

agent-web: 47/47 テスト合格（2026-03-06 00:56 JST 最終確認）

Python: 50/50 pytest 合格

Daily Digest 実行実績

日付	キーワード数	論文数	JSON サイズ	MD サイズ

2026-03-05	5	49	4977 B	3611 B

2026-03-06	5	49	4459 B	3027 B

6\. 未実施タスク（優先度順）

高優先度 🔴

ID	タスク	備考

P3-6	LightRAG 統合	jarvis\_core の LightRAG をエージェント Web に接続。graph persistence で asyncio.CancelledError の既知問題あり

E2E-1	フル E2E テスト	ブラウザ経由でパイプライン→DB 保存→Obsidian 出力→PDF アーカイブを通しで検証

GIT-1	未コミットファイルの確認	最後のセッションで memory-store.js, memory.js, chat.js 修正, digest.test.js 追加, server.js 修正が未コミットの可能性あり。git status で確認し、未追跡ファイルがあれば即コミット

中優先度 🟡

ID	タスク	備考

UI-3	テキストキャラクターグロー	文字単位の発光アニメーション

UI-4	Markdown ヘッダー slide-down	h1〜h6 のスライドダウン

UI-5	テーブル行 fade-in	テーブル描画時の行フェードイン

UI-6	Reasoning アコーディオン	思考過程の折りたたみ UI

UI-7	階層タスクツリー	タスク進行の階層表示

MEM-1	メモリ UI	/api/memory を使ったブラウザ上のファクト管理画面

README-1	ルート README 更新	Agent-Web セクション（メモリ, Daily Digest, Phase 3 機能）を追記

低優先度 🟢

ID	タスク	備考

CHAT-1	チャット履歴エクスポート	JSON/Markdown 形式

CHAT-2	ファイルアップロード	PDF 等のアップロード→解析

THEME-1	ダーク/ライトテーマ切替	現在はダークのみ

WS-1	WebSocket アップグレード	SSE → WebSocket（双方向通信）

PIPE-UI	パイプライン UI トリガー	チャットからパイプライン実行

RC-1	リサーチコンパイラ	複数 API 検索→ランキング→知見抽出→教科書風チャプター生成→Obsidian 出力→インクリメンタル更新

7\. Git コミット履歴（直近主要）

b01577dd feat: Phase 3 foundation - papers CRUD, digest-to-obsidian, CI workflow, rate limit fixes, pipeline DB save

4d6c7e9e feat: P3-3 PDF archiver, P3-4 Zotero sync, P3-5 ChromaDB bridge

643c7d74 feat(agent-web): Phase 1 UI – dark/gold, particles

3938883a feat(agent-web): session memory – H-2

37051d0d docs: add Agent-Web section – I-3

38587e79 feat: Agent-Web v1.0.0

edd4d0cf (tag: v2.0.0) D7: v2.0.0 release

注意: H-2 chat 統合、H-3 memory-store、Memory API、UI Phase 2 アニメーション、テスト拡張（47 テスト）が未コミットの可能性あり。起動時に必ず git status を実行すること。



8\. 既知の問題と注意事項

問題	深刻度	対処法

npm test で spawn EPERM	低	Codex App サンドボックス内でのみ発生。PowerShell 直接実行では全パス。または node --test --test-isolation=none tests/\*.test.js を使用

OPENAI\_API\_KEY が空	低	OpenAI 系機能は動作しない。gemini-2.0-flash で代替

DEEPSEEK\_API\_KEY が空	低	DeepSeek フォールバック不可

claude-opus-4.6 で 400 エラー	中	claude-sonnet-4.6 を使用する

gpt-5.1 で 400 エラー	中	gpt-4.1 を使用する

Gemini レートリミット	中	15 RPM 制限。concurrency 1, delay 4500ms で対策済み

Semantic Scholar レートリミット	中	100 req/5 min。1500ms 遅延 + 429 リトライで対策済み

PubMed レートリミット	低	3 req/s。350ms 遅延で対策済み

LightRAG asyncio.CancelledError	中	graph persistence 失敗。P3-6 で対応予定

Datalab API 403	低	PyMuPDF にフォールバック

H: ドライブ切断	低	Google Drive が切断されると Obsidian / jarvis-data パスが無効に。再接続で復旧

agents.py vs agents/ 競合	低	jarvis\_core.agents.orchestrator をインポートしない

Scrapling css\_first 未定義	低	browse.py 利用時に注意

PowerShell で $1 消失	中	JS 内の $1 が PowerShell の here-string で消える。String.fromCharCode(36)+"1" または一時 .js ファイル経由で回避

LF/CRLF 警告	低	git push 時に表示される。動作影響なし

config.yaml Zotero api\_key 空	低	.env の ZOTERO\_API\_KEY とは別管理

9\. 絶対ルール（必ず守ること）

agent-web 外のファイルを変更しない（Web タスクの場合）

python -c で複雑なコードを実行しない — 必ず .py ファイルを作成して実行

jarvis\_cli/init.py は完全上書きのみ（部分編集禁止）

jarvis\_core.agents.orchestrator をインポートしない（agents.py と agents/ の競合）

無料枠 API のみ使用（Gemini free tier, Semantic Scholar, PubMed）

ESM モジュール（import/export）を使用、path.join() で Windows パス処理

PowerShell here-string 内に JS の $ を書かない

npm install は npm ci または npm install --save で、余計な依存を増やさない

コミットメッセージは conventional-commit 形式（feat:, fix:, docs:, test: 等）

.env を絶対に git commit しない

Codex App の sandbox 内では spawn EPERM が出るため、テストは PowerShell 直接実行で確認

ファイル作成は notepad ファイル名 → 貼り付け → 保存 の手順（PowerShell の複雑なヒアドキュメントを避ける）

10\. スモークテスト手順（セッション開始時に必ず実行）

Step 1: Git 状態確認

Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

git status

git log --oneline -5

Step 2: Python バックエンド確認

Copy.venv\\Scripts\\Activate.ps1

python --version      # → 3.11.9

python -m jarvis\_cli --help   # → 22 コマンド表示

python -m pytest tests/ -q    # → 50 passed

Step 3: Agent-Web テスト

Copycd agent-web

npm test              # → 47 passed, 0 failed

（spawn EPERM の場合: node --test --test-isolation=none tests/\*.test.js）



Step 4: サーバー起動

Copynpm run dev           # → JARVIS Agent Web v1.0.0 running at http://localhost:3000

Step 5: ブラウザ確認

http://localhost:3000 を開く

Chat タブ: メッセージ送信→応答確認

Pipeline タブ: 「Run Daily Digest」→進捗表示→完了確認

Digest History テーブルにエントリがあることを確認

Step 6: papers-repository 確認

Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

node -e "import('./agent-web/src/db/papers-repository.js').then(m => { console.log('countPapers:', m.countPapers()); console.log('exports:', Object.keys(m)); }).catch(e => console.log('ERROR:', e.message))"

期待結果: countPapers: 0（または保存済み論文数）、9 関数のリスト



Step 7: タスクスケジューラ確認

Copyschtasks /query /tn "JARVIS-DailyDigest"

期待結果: 次回実行 07:00、ステータス「準備完了」



11\. Codex App 操作ガイド

エージェント定義

explorer: read-only、コードベース調査・ファイル構造確認用

worker: 実装用、ファイル作成・修正

reviewer: コードレビュー、バグ発見、セキュリティチェック

並列実行パターン

独立した 3 タスクを 1 つのプロンプトに === TASK A === === TASK B === === TASK C === で記述

Codex App に貼り付けて送信 → 3 タスク同時実行

全完了後にローカルで npm test → git add -A → git commit → git push

依存関係のあるタスクは前のバッチ完了後に次バッチを投入

注意事項

server.js や index.html を複数タスクが同時変更すると競合する → 片方を先にコミット

sandbox 内の spawn EPERM はコードの問題ではない

worker の sandbox: workspace-write 設定で agent-web/ 配下のみ書き込み可能

12\. 技術判断メモ

ESM: agent-web 全体が ESM（import/export）。package.json に "type": "module" 設定済み

dotenv: server.js 起動時に ../.env を読み込み。CLI 実行時は daily-digest.js 内で dotenv.config({path: '../../.env'})

SSE パターン: pipeline.js / digest.js が Server-Sent Events で進捗送信。フロントは EventSource（GET のみ）

better-sqlite3: 同期 API のため SQLITE\_BUSY リスク低。WAL モード未設定

Copilot API: copilot-api パッケージ（localhost:4141）経由で GitHub Copilot にアクセス。デフォルトモデル claude-sonnet-4.6

フォールバックチェーン: Copilot API → Gemini API（LiteLLM 経由）

PDF アーカイブ: Unpaywall API（doi ベース）→ 直接 URL → 失敗時スキップ

13\. 主要パッケージバージョン

Node.js (agent-web)

express: ^5.1.0

better-sqlite3: ^11.10.0

copilot-api: latest

dotenv: ^16.6.1

eventsource-parser: ^3.0.1

js-yaml: ^4.1.1

uuid: ^11.1.0

nodemon: ^3.1.0 (dev)

Python

jarvis-research-os==1.0.0

google-genai==1.65.0

litellm==1.82.0

chromadb (latest)

langgraph (latest)

sentence-transformers (all-MiniLM-L6-v2)

pyzotero, rapidfuzz, pydantic-ai, instructor

streamlit==1.54.0

pytest (latest)

14\. 次セッションの推奨アクション

GIT-1: git status で未コミットファイルを確認し、あれば即コミット

P3-6: LightRAG 統合（chroma-bridge.js の拡張）

E2E-1: ブラウザ経由フルパイプラインテスト

MEM-1: メモリ管理 UI の実装

README-1: ルート README の Agent-Web セクション更新

15\. ファイル変更履歴（本セッション: 2026-03-05 〜 2026-03-06）

ファイル	操作	内容

agent-web/src/db/papers-repository.js	新規	papers CRUD（9 関数）

agent-web/src/db/memory-store.js	新規	facts + user\_preferences テーブル

agent-web/src/db/chroma-bridge.js	新規	Python ChromaDB subprocess ブリッジ

agent-web/src/db/create-papers-table.js	新規	papers テーブルマイグレーション

agent-web/src/skills/digest-to-obsidian.js	新規	Digest→Obsidian エクスポート

agent-web/src/skills/pdf-archiver.js	新規	PDF ダウンロード+アーカイブ

agent-web/src/skills/zotero-sync.js	新規	Zotero Web API v3 同期

agent-web/src/routes/memory.js	新規	Memory API エンドポイント

agent-web/src/routes/chat.js	修正	memory-store 統合、systemPromptWithContext、研究論文コンテキスト注入

agent-web/src/routes/pipeline.js	修正	DB 保存（insertPapers）、PDF アーカイブ（archivePapers）追加

agent-web/src/llm/gemini-summarizer.js	修正	concurrency 1, delayMs 4500

agent-web/src/llm/paper-search.js	修正	delay ヘルパー、レートリミット遅延、429 リトライ

agent-web/src/skills/daily-digest.js	修正	exportDigestToObsidian 呼び出し追加

agent-web/src/server.js	修正	memoryRouter 登録

agent-web/public/js/app.js	修正	text-reveal、activity-dot アニメーション

agent-web/public/css/styles.css	修正	textReveal、pulse、slideInLeft キーフレーム

agent-web/tests/digest.test.js	修正	19 テストに拡張（memory-store、chat、各モジュール）

agent-web/package.json	修正	test:ci スクリプト追加

.github/workflows/test.yml	新規	CI/CD ワークフロー

run-daily-digest.bat	新規	タスクスケジューラ用バッチ

HANDOVER\_v15.md	新規	Phase 3 完了引き継ぎ

HANDOVER\_v16.md	新規	★ この文書

この引き継ぎ書は 2026-03-06 01:00 JST 時点の状態を正確に反映している。





---



\## 次チャット開始時のコピペ用プロンプト



以下を次のチャットの最初のメッセージとしてそのまま貼り付けてください：



---



あなたは JARVIS Research OS + Agent-Web プロジェクトの開発を引き継ぐ AI エージェントです。



プロジェクト情報

GitHub: https://github.com/kaneko-ai/jarvis-ml-pipeline (main ブランチ)

引き継ぎ書: https://github.com/kaneko-ai/jarvis-ml-pipeline/blob/main/HANDOVER\_v16.md

現在の状態（2026-03-06 01:00 JST 時点）

Python CLI v2.0.0: 22 コマンド、pytest 50/50 合格

Agent-Web: Express v5 + better-sqlite3、47/47 テスト合格

Phase 0〜3 全完了: Daily Digest（5キーワード×10件/日, Windows 07:00 自動実行）、papers CRUD（9関数）、PDF アーカイバ、Zotero 同期、ChromaDB ブリッジ

H-2 セッションメモリ + H-3 永続メモリ + Memory API 実装済み

UI Phase 1 + Phase 2 部分（text-reveal, activity-dot, slideInLeft）完了

CI/CD: GitHub Actions ワークフロー設定済み

Digest 実績: 2026-03-05（49論文）、2026-03-06（49論文）

環境

Windows 11, Node v24.13.1, Python 3.11.9

プロジェクト: C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline

ポート: 3000（Express）, 4141（Copilot API）

LLM: gemini-2.0-flash（デフォルト）, claude-sonnet-4.6（チャット）

.env にAPIキー設定済み（GEMINI\_API\_KEY, ZOTERO\_API\_KEY 等）

Codex App: explorer / worker / reviewer の 3 エージェント

最初にやること

HANDOVER\_v16.md を上記 URL から読み込み、完全に理解する

セクション 10 のスモークテスト手順を提示する（特に git status で未コミットファイルの有無を確認）

セクション 6 の未実施タスクから、優先度の高いものを提案する

絶対ルール（セクション 9）と既知の問題（セクション 8）を確認し遵守する

絶対ルール（要約）

agent-web/ 外のファイルを変更しない（Web タスクの場合）

無料枠 API のみ使用

ESM + path.join でWindows パス処理

.env を git commit しない

conventional-commit 形式

