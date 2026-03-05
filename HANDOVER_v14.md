\# HANDOVER\_v14.md — JARVIS ML Pipeline 引き継ぎ書

> \*\*作成日\*\*: 2026-03-05 20:40 JST

> \*\*作成者\*\*: Claude Opus 4.6 + ユーザー (kaneko yu)

> \*\*前回引き継ぎ\*\*: HANDOVER\_v13.md

> \*\*対象\*\*: 次チャットの AI エージェント（Claude / GPT / Codex 等）



---



\## 1. プロジェクト概要



\*\*JARVIS ML Pipeline\*\* は Windows 11 上で動作する研究論文の自動収集・要約パイプラインである。

Express + better-sqlite3 の Web アプリ（agent-web）をコアとし、PubMed・Semantic Scholar・OpenAlex から論文を検索、Gemini 2.0 Flash で要約、SQLite に保存する。

OpenAI Codex App（Windows GUI）を並列エージェントとして採用し、explorer / worker / reviewer の 3 エージェントで開発タスクを並列実行する体制が確立済み。



---



\## 2. 環境情報（2026-03-05 時点で動作確認済み）



| 項目 | 値 |

|---|---|

| OS | Windows 11 |

| Node.js | v24.13.1 |

| npm | 11.8.0 |

| Git | 設定済み（safe.directory 登録済み） |

| Python | 3.x（scripts/ 用、agent-web には不要） |

| プロジェクトルート | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| agent-web ルート | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web` |

| GitHub リポジトリ | `https://github.com/kaneko-ai/jarvis-ml-pipeline.git` (main ブランチ) |

| Codex App | インストール・設定完了、3 エージェント（explorer, worker, reviewer）定義済み |

| LLM モデル | gemini/gemini-2.0-flash（config.yaml の llm.default\_model） |

| GEMINI\_API\_KEY | .env に設定済み（AIzaSyCK...）、agent-web から `require('dotenv').config({path:'../.env'})` で読み込み |

| Obsidian Vault | `H:\\マイドライブ\\obsidian-vault` |

| データ保存先 | Google Drive: `H:\\マイドライブ\\jarvis-data\\` |



\### .env ファイル（プロジェクトルート直下、1 ファイルのみ）

Copy

ZOTERO\_API\_KEY=wc3GxeCPThtkWJnvVJQsLtLb ZOTERO\_USER\_ID=16956010 OPENAI\_API\_KEY=（空） DEEPSEEK\_API\_KEY=（空） LLM\_MODEL=gemini/gemini-2.0-flash DATALAB\_API\_KEY=ng2yRJcuRfpvc0mCRwENWwGucyfLq5eTOXMTBB7eeyY GEMINI\_API\_KEY=AIzaSyCK...（実値は .env 参照）





\### config.yaml（プロジェクトルート直下）

```yaml

obsidian:

&nbsp; vault\_path: "H:\\\\マイドライブ\\\\obsidian-vault"

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

&nbsp; logs\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\logs"

&nbsp; exports\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\exports"

&nbsp; pdf\_archive\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\pdf-archive"

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

├── .env                          # API キー（GEMINI\_API\_KEY 含む）

├── .gitignore                    # \*.har 含む

├── config.yaml                   # 全体設定（digest セクション追加済み）

├── scripts/                      # Python ユーティリティ（80+ ファイル）

├── agent-web/

│   ├── package.json              # "test": "node --test tests/\*.test.js"

│   ├── data/

│   │   ├── \*.json                # パイプライン実行結果

│   │   └── digests/              # Daily Digest 出力先（自動作成）

│   ├── public/

│   │   ├── index.html            # 3 タブ UI（Chat | Pipeline | Monitor）

│   │   ├── css/styles.css        # ダークテーマ（#0a0a0a, #00ff88 アクセント）

│   │   └── js/app.js             # フロントエンド全ロジック

│   ├── src/

│   │   ├── server.js             # Express メイン（全ルート登録済み）

│   │   ├── db/

│   │   │   └── jarvis.db         # SQLite（pipeline\_runs テーブル含む）

│   │   ├── llm/

│   │   │   ├── paper-search.js   # PubMed + Semantic Scholar + OpenAlex 検索

│   │   │   ├── gemini-summarizer.js  # Gemini 2.0 Flash 要約（リトライ付き）

│   │   │   ├── parallel-runner.js    # API プール管理（apiPool:4, geminiPool:3, copilotPool:1）

│   │   │   ├── copilot-bridge.js

│   │   │   ├── jarvis-tools.js

│   │   │   ├── python-bridge.js

│   │   │   └── llm\_caller.py

│   │   ├── routes/

│   │   │   ├── pipeline.js       # SSE 7 ステップパイプライン

│   │   │   ├── monitor.js        # /status, /health, /history

│   │   │   ├── digest.js         # /run, /history, /report/:filename

│   │   │   └── （chat.js, sessions.js, models.js, skills.js, mcp.js, usage.js）

│   │   ├── skills/

│   │   │   ├── daily-digest.js   # Daily Digest メインロジック

│   │   │   └── skill-registry.js

│   │   ├── middleware/

│   │   └── mcp-bridge/

│   └── tests/

│       ├── pipeline.test.js      # 21 テスト（全パス）

│       ├── database.test.js

│       └── api.test.js

└── .codex/

&nbsp;   └── agents/

&nbsp;       ├── explorer.toml

&nbsp;       ├── worker.toml

&nbsp;       └── reviewer.toml

4\. API エンドポイント一覧（server.js 登録順）

メソッド	パス	説明	状態

POST	/api/chat/stream	チャット（SSE）	✅ 動作確認済み

GET	/api/sessions	セッション一覧	✅

GET	/api/models	LLM モデル一覧	✅

GET	/api/skills	スキル一覧	✅

GET/POST	/api/mcp/\*	MCP ブリッジ	✅

GET	/api/usage	使用量	✅

GET	/api/pipeline/run?query=…\&limit=…	パイプライン実行（SSE 7 ステップ）	✅

GET	/api/pipeline/history	パイプライン履歴	✅

GET/POST	/api/digest/run	Daily Digest 実行（SSE）	✅ UI 表示確認済み

GET	/api/digest/history	Digest 履歴	✅

GET	/api/digest/report/:filename	Digest レポート取得	✅

GET	/api/monitor/status	システム状態	✅

GET	/api/monitor/health	ヘルスチェック	✅

GET	/api/monitor/history	パイプライン履歴（Monitor 用）	✅

GET	/api/health	簡易ヘルス	✅

—	/data/\*	静的ファイル配信（パイプライン結果 JSON）	✅

5\. 完了済みタスク（Phase 0 + Phase 1）

Phase 0: 環境構築

&nbsp;Codex App インストール・設定・3 エージェント定義

&nbsp;config.toml の config\_file パス修正

&nbsp;Git safe.directory 設定

&nbsp;better-sqlite3 インストール

&nbsp;paper-search.js 動作確認（PubMed 3 件 + Semantic Scholar 3 件取得成功）

&nbsp;大容量 .har ファイル除去（.gitignore 追加、git push --force-with-lease 成功）

Phase 1: コア機能実装

&nbsp;タブ UI: Chat | Pipeline | Monitor の 3 タブナビゲーション

&nbsp;parallel-runner.js: API プール管理（apiPool:4, geminiPool:3, copilotPool:1）

&nbsp;pipeline.js: SSE 7 ステップ（検索→重複除去→スコアリング→ソート→Gemini 要約→JSON 生成→保存）

&nbsp;monitor.js: /status（Copilot API, DB, uptime, nodeVersion）, /health, /history

&nbsp;Pipeline フロントエンド: 検索フォーム、ステップカード、結果テーブル（要約表示付き）、履歴

&nbsp;Monitor フロントエンド: ステータスカード 4 枚、10 秒自動更新、履歴テーブル

&nbsp;Gemini 要約モジュール: gemini-summarizer.js（レートリミット 4000ms、429/500/503 リトライ、AbortController 30s タイムアウト）

&nbsp;エラーハンドリング強化: 各ステップ try/catch、全体 120s タイムアウト、ソース片方失敗時続行、保存失敗時 warning

&nbsp;テスト: 6 スイート・21 テスト全パス（API 5, DB CRUD 5, parallel-runner 4, gemini-summarizer 3, pipeline 2, monitor 2）

&nbsp;パイプライン初回実行成功: "PD-1 immunotherapy" で 50 件取得、"CRISPR gene therapy" で 50 件取得＋Gemini 要約 10 件

Phase 2: Daily Digest（部分完了）

&nbsp;config.yaml: digest セクション追加（5 キーワード: CRISPR gene therapy, PD-1 immunotherapy, PD-1, spermidine, cancer）

&nbsp;daily-digest.js: メインロジック作成（キーワード検索→マージ→重複除去→要約→SQLite 保存→MD/JSON 出力）

&nbsp;digest.js ルート: /api/digest/run（SSE）, /history, /report/:filename

&nbsp;フロントエンド: Pipeline タブ内に Daily Digest セクション（Run ボタン、結果表示、履歴テーブル）

&nbsp;Daily Digest 初回実行テスト: 未実施（Run Daily Digest ボタンを押して動作確認が必要）

&nbsp;Windows タスクスケジューラ登録: 毎日 07:00 に自動実行する設定が未実施

6\. 未実施タスク（優先度順）

Phase 2 残り

ID	タスク	優先度	備考

P2-1	Daily Digest 初回実行テスト	🔴 高	ブラウザで Run Daily Digest ボタンを押す。5 キーワード × 10 件 = 最大 50 件検索 → 要約 5 件。約 1-2 分かかる

P2-2	Windows タスクスケジューラ登録	🟡 中	schtasks /create で毎日 07:00 に node agent-web/src/skills/daily-digest.js を実行

P2-3	Digest 結果の Obsidian 連携	🟡 中	digest-YYYY-MM-DD.md を Obsidian vault にコピー

Phase 3: 高度な機能

ID	タスク	優先度	備考

P3-1	SQLite スキーマ拡張	🟡 中	papers テーブル追加（title, authors, journal, year, abstract, summary, source, score, created\_at）

P3-2	重複検知の永続化	🟡 中	新規論文のみ通知する仕組み

P3-3	PDF ダウンロード＋アーカイブ	🟢 低	pdf\_archive\_dir に保存

P3-4	Zotero 連携	🟢 低	ZOTERO\_API\_KEY は設定済み、コレクション追加機能

P3-5	ChromaDB ベクトル検索	🟢 低	類似論文検索

P3-6	LightRAG 統合	🟢 低	論文ナレッジグラフ

継続的改善

ID	タスク	備考

C-1	テスト追加（digest 関連）	daily-digest.js, digest.js ルートのテスト

C-2	CI/CD 設定	GitHub Actions で npm test 自動実行

C-3	HANDOVER\_v14.md をリポジトリにコミット	この文書自体

7\. 既知の問題と注意事項

問題	状態	対処法

npm test で spawn EPERM	Codex App サンドボックス内でのみ発生。PowerShell 直接実行では全パス	Codex App 外で npm test を実行する

OPENAI\_API\_KEY が空	OpenAI API を使用する機能は動作しない	必要時に .env に設定

DEEPSEEK\_API\_KEY が空	DeepSeek フォールバックは動作しない	必要時に .env に設定

agent-web/.env は存在しない	.env はプロジェクトルート直下の 1 ファイルのみ	dotenv で ../.env を読み込む

data/ 内の大量 JSON	パイプライン実行ごとに蓄積	定期的に古いファイルを削除するか prune スクリプトを作成

config.yaml の Zotero api\_key が空文字	.env の ZOTERO\_API\_KEY とは別管理	将来的に統一が望ましい

8\. サーバー起動・テスト手順

Copy# サーバー起動

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web"

npm run dev

\# → http://localhost:3000 でアクセス



\# テスト実行（21 テスト全パス想定）

npm test



\# Daily Digest 手動実行（CLI）

node src/skills/daily-digest.js



\# パイプライン結果確認

Get-ChildItem data/

Get-ChildItem data/digests/



\# Git 操作

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

git add -A

git commit -m "メッセージ"

git push origin main

9\. Codex App 操作ガイド

エージェント: explorer（read-only 調査用）, worker（実装用）, reviewer（コードレビュー用）

並列実行: 2 スレッド同時作成 → 両方完了後にコミット＆プッシュ

コンフリクト対策: server.js や index.html を両スレッドが変更する場合、片方を先にコミットしてからもう片方をコミット

sandbox 制限: spawn EPERM は Codex App 固有の問題でコード自体に問題はない

コミット方法: サイドバーでスレッド選択 →「コミットとプッシュ」→ 自動生成メッセージで確定

10\. 即座に実行すべきアクション

ステップ 1: Daily Digest 初回実行テスト

サーバーが起動中であることを確認（npm run dev）

ブラウザで http://localhost:3000 → Pipeline タブ

「Daily Digest」セクションの 「Run Daily Digest」 ボタンをクリック

進捗メッセージを確認（5 キーワード × 10 件検索 → 要約 → 保存）

完了後、結果が表示されるか確認

agent-web/data/digests/ に digest-2026-03-05.md と .json が作成されたか確認

ステップ 2: Windows タスクスケジューラ登録

Copyschtasks /create /tn "JARVIS-DailyDigest" /tr "node \\"C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\agent-web\\src\\skills\\daily-digest.js\\"" /sc daily /st 07:00 /f

ステップ 3: テスト追加（digest 関連）

Codex App で新しいスレッドを作成し、agent-web/tests/digest.test.js を作成。daily-digest.js の import 確認、runDailyDigest 関数の存在確認、digest.js ルートの Router export 確認をテスト。



ステップ 4: SQLite スキーマ拡張

papers テーブルを作成し、パイプライン結果を永続化。重複検知用のインデックスを追加。



ステップ 5: コミット

Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

git add -A

git commit -m "docs: HANDOVER\_v14.md (Phase 1 complete, Phase 2 daily-digest implemented)"

git push origin main

11\. Git コミット履歴（直近）

ec63ec07 – feat: add tabbed navigation + parallel-runner, remove large .har file

（以降、Phase 1 の各コミットが続く）

\- feat: register monitorRouter in server.js

\- feat: pipeline + monitor UI complete, serve data/ as static

\- feat: Gemini summarization step + summary display in pipeline results

\- feat: error handling + retry logic, add 21 tests (all pass)

\- feat: daily-digest + digest API + digest UI（最新）

12\. 技術的な判断メモ

ESM vs CJS: agent-web は ESモジュール（import/export）を使用。package.json に "type": "module" は未設定だが、.js ファイル内で import 構文を使用している箇所あり。server.js は ESM。

dotenv の読み込み: server.js が起動時に .env を読み込むため、ルートの子プロセスからは process.env.GEMINI\_API\_KEY でアクセス可能。CLI 実行時は daily-digest.js 内で dotenv.config({path: '../../.env'}) または相対パスで読み込む。

静的ファイル配信: public/ と data/（/data/\*）の両方を Express の express.static で配信。

SSE パターン: pipeline.js と digest.js は Server-Sent Events で進捗を送信。フロントエンドは EventSource で受信。ブラウザの EventSource は GET のみ対応のため、フロントは GET /api/digest/run を使用（サーバーは POST も受付可）。

この引き継ぎ書は 2026-03-05 20:40 JST 時点の状態を正確に反映しています。

