\# HANDOVER\_v5.md — JARVIS Research OS 引き継ぎ書 v5



\*\*作成日\*\*: 2026-03-02

\*\*前版\*\*: HANDOVER\_v4.md（2026-03-02、コミット 5c043b02 時点）

\*\*対象リポジトリ\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline

\*\*ブランチ\*\*: `main`

\*\*最新プッシュ済みコミット\*\*: `9220dd5a` — "C-4: Multi-Agent Orchestrator - pipeline (search/evidence/score/summarize/review), no orchestrator.py dependency"（2026-03-02T11:01:32Z）

\*\*関連リポジトリ\*\*: https://github.com/kaneko-ai/zotero-doi-importer（A-6 完了済み、コミット `0cb2447`）



\*\*本書の目的\*\*: この文書を読んだ AI または開発者が、追加の質問なしに環境理解→残タスク実装まで100%再現・継続できることを保証する。



---



\## 1. プロジェクト概要



JARVIS Research OS は、系統的文献レビュー（Systematic Literature Review）を自動化するローカルファースト AI アシスタント。CLI コマンド 1 つで「論文検索 → 重複除去 → エビデンス判定 → スコアリング → LLM日本語要約 → Obsidian ノート作成 → Zotero 登録 → PRISMA図生成 → BibTeX出力」を一括実行できる。



\*\*主な利用者\*\*: 大学院生（プログラミング初学者、Windows環境）

\*\*主な用途\*\*: PD-1免疫療法、スペルミジン、免疫老化・オートファジーなどの研究テーマに関する文献調査



---



\## 2. 開発環境（実機ステータス 2026-03-02 時点）



| 項目 | 値 |

|------|-----|

| OS | Windows 11 |

| シェル | PowerShell 5.1 |

| Python | 3.12.3 |

| Node.js | v24.13.1 |

| プロジェクトパス | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| venv パス | `.venv`（プロジェクトルート直下） |

| venv 有効化 | `.\\.venv\\Scripts\\Activate.ps1` |

| Python 実体 | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\.venv\\Scripts\\python.exe` |

| Obsidian Vault | `C:\\Users\\kaneko yu\\Documents\\ObsidianVault` |

| conda 環境名 | `jarvis-research-os`（PowerShell プロンプトに表示される） |



\### 2.1 環境変数（.env）



`.env` はプロジェクトルートに存在し、Git 追跡外（`.gitignore` で除外済み）。



Copy

GEMINI\_API\_KEY=<39文字のGemini APIキー> LLM\_PROVIDER=gemini ZOTERO\_API\_KEY=<2026-03-02に新規発行済み> ZOTERO\_USER\_ID=16956010





\### 2.2 インストール済み主要パッケージ（.venv内）



jarvis-research-os==1.0.0（`pip install -e .` でインストール）、google-genai==1.65.0、python-dotenv==1.2.2、rank-bm25==0.2.2、sentence-transformers（all-MiniLM-L6-v2 モデル自動DL済み）、pyzotero、requests==2.32.5、streamlit==1.54.0、rapidfuzz==3.14.3、scikit-learn（Active Learning用）、pyyaml、scrapling（Browser Agent用、Scrapling Selector ライブラリ）、beautifulsoup4。



\### 2.3 venv内の pip に関する重要な注意



過去に venv に pip が存在せず、`pip install` がシステム Python にインストールされていた問題あり。`python -m ensurepip --upgrade` で修復済み。\*\*今後のルール: パッケージインストールには必ず `python -m pip install <package>` を使用すること。\*\*



\### 2.4 未インストール・接続不可のコンポーネント



| コンポーネント | 状態 | 備考 |

|------------|------|------|

| Ollama（ローカルLLM） | 未起動・未インストール | `use\_llm=False` で回避中 |

| pandas 3.0.0 | インストール失敗 | 現在の機能では不要 |



---



\## 3. タスク完了状況の全体マップ



\### v2 タスク（全8件 — 全完了・マージ済み）



| タスク | 内容 | 状態 |

|--------|------|------|

| T1-2 | UnifiedSourceClient を CLI に接続 | ✅ 完了 |

| T1-3 | セキュリティ整備（.gitignore, backup.ps1） | ✅ 完了 |

| T2-1 | EnsembleClassifier を CLI に接続 | ✅ 完了 |

| T2-2 | Obsidian Vault 直接出力 | ✅ 完了 |

| T3-1 | semantic-search コマンド | ✅ 完了 |

| T3-2 | contradict コマンド | ✅ 完了 |

| T3-3 | Zotero 連携（zotero-sync） | ✅ 完了 |

| T4-1 | pipeline コマンド（全工程一括実行） | ✅ 完了 |



\### Phase A: 高優先度（全6件 — 全完了）



| タスク | 内容 | 状態 | コミット | 備考 |

|--------|------|------|---------|------|

| A-6 | zotero-doi-importer の .env 削除 | ✅ 完了 | `0cb2447` (別repo) | git rm --cached .env |

| A-1 | LLM要約の pipeline 統合 | ✅ 完了 | `5c043b02` | Gemini API で日本語要約生成 |

| A-2 | Semantic Scholar 429 リトライ | ✅ 完了 | `5c043b02` | 指数バックオフ（5s→10s→30s） |

| A-3 | 重複除去の精度向上（fuzzy match） | ✅ 完了 | `5c043b02` | rapidfuzz.fuzz.ratio >= 90 |

| A-4 | PRISMA ダイアグラムの pipeline 統合 | ✅ 完了 | `5c043b02` | Mermaid .mmd + Markdown .md |

| A-5 | BibTeX の pipeline 統合 | ✅ 完了 | `5c043b02` | .bib ファイル出力 |



\### Phase B: 中優先度（全6件 — 全完了）



| タスク | 内容 | 状態 | コミット | 備考 |

|--------|------|------|---------|------|

| B-5 | Obsidian ノートテンプレート強化 | ✅ 完了 | `18941276` | Evidence Level バッジ、study\_type、keywords追加 |

| B-3 | Paper Scoring CLI + pipeline 統合 | ✅ 完了 | `18941276` | Grade A-F で評価 |

| B-1 | Citation Stance 分類 | ✅ 完了 | `18941276` | SUPPORT/CONTRAST/NEUTRAL/MENTION |

| B-2 | Contradiction 検出の改善（LLM対応） | ✅ 完了 | `18941276` | --use-llm フラグ |

| B-4 | Active Learning Screening | ✅ 完了 | `18941276` | --auto モードでキーワードベース自動ラベリング |

| B-6 | Streamlit Dashboard 拡張 | ✅ 完了 | `024a1a86` | logs一覧、contradictions表示、統計 |



\### Phase C: 低優先度（全6件 — 全完了、プッシュ済み）



| タスク | 内容 | 状態 | コミット | 備考 |

|--------|------|------|---------|------|

| C-5 | arXiv/Crossref の UnifiedSourceClient 統合 | ✅ 完了 | `024a1a86` | SourceType.ARXIV/CROSSREF 追加済み |

| C-6 | Zotero コレクション指定 | ✅ 完了 | `c7f24014`, `f13ddbf4` | config.yaml の zotero.collection 活用 |

| C-2 | Browser Agent | ✅ 完了 | `5564623e` | Scrapling parser、PubMed/arXiv/Generic対応 |

| C-3 | Skills System | ✅ 完了 | `cf73f002` | 9スキル自動検出、CLI list/match/show/context |

| C-1 | MCP Hub 統合 | ✅ 完了 | `7320bbe6` | 5サーバー15ツール、ローカルAPI実行 |

| C-4 | Multi-Agent Orchestrator | ✅ 完了 | `9220dd5a` | 5エージェント pipeline（search→evidence→score→summarize→review） |



---



\## 4. ローカルとリモートの同期状態（重要）



\*\*リモート最新コミット\*\*: `9220dd5a`（C-4: Multi-Agent Orchestrator）



\*\*ローカルに未プッシュの変更がある可能性\*\*: C-4 のコミットは「ローカルで `write\_c4\_cli\_v2.py` を実行→テスト成功」まで確認したが、\*\*ユーザーが `git commit` \& `git push` を実行したかは未確認\*\*。セッション開始時に以下で確認すること：



```powershell

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1

git status

git log --oneline -5

もし orchestrate.py が unstaged changes として表示される場合は以下を実行：



Copygit add jarvis\_cli/\_\_init\_\_.py jarvis\_cli/orchestrate.py

git commit -m "C-4: Multi-Agent Orchestrator - pipeline (search/evidence/score/summarize/review), no orchestrator.py dependency"

git push origin main

5\. 既知の構造的問題（必読）

5.1 agents.py と agents/ ディレクトリの衝突

リポジトリに jarvis\_core/agents.py（34KB のファイル）と jarvis\_core/agents/（ディレクトリ、中に orchestrator.py 1ファイル）が同時に存在する。Python ではファイル agents.py が優先されるため、from jarvis\_core.agents.orchestrator import ... は 常に失敗する（ModuleNotFoundError: 'jarvis\_core.agents' is not a package）。



回避策（C-4 で採用）: orchestrator.py を import せず、jarvis\_cli/orchestrate.py で直接 UnifiedSourceClient、grade\_evidence、score\_papers を呼び出す。今後も jarvis\_core.agents.orchestrator は import しないこと。



5.2 Scrapling の API（css\_first は存在しない）

Scrapling の Selector オブジェクトには css\_first() メソッドが存在しない。代わりに css("selector") でリストを取得し \[0] でアクセスする。browse.py ではヘルパー \_first(page, selector) でラップ済み。



5.3 PowerShell 5.1 の JSON エスケープ問題

PowerShell 5.1 ではコマンドラインに JSON を渡す際、" のエスケープが壊れる。--params '{"key":"val"}' も --params "{\\"key\\":\\"val\\"}" も失敗する場合がある。解決策: mcp invoke コマンドは --params-file <file.json> オプションを実装済み。JSON はファイル経由で渡すこと。



5.4 init.py の編集ルール

jarvis\_cli/\_\_init\_\_.py は全文上書きのみ。部分挿入（文字列の replace や insert）は過去に複数回失敗している。write\_\*.py スクリプトで全ファイルを書き出す方式を厳守すること。



6\. 現在の CLI コマンド一覧（20コマンド）

コマンド	使用例	状態

search	jarvis search "PD-1" --max 5 --sources pubmed,s2,openalex,arxiv,crossref	✅

merge	jarvis merge file1.json file2.json -o merged.json	✅

note	jarvis note input.json --provider gemini --obsidian	✅

citation	jarvis citation input.json	✅

citation-stance	jarvis citation-stance input.json \[--no-llm]	✅

prisma	jarvis prisma file1.json file2.json -o prisma.md	✅

evidence	jarvis evidence input.json	✅

score	jarvis score input.json	✅

screen	jarvis screen input.json \[--auto] \[--batch-size 5] \[--budget 50]	✅

obsidian-export	jarvis obsidian-export input.json	✅

semantic-search	jarvis semantic-search "query" --db file.json --top 10	✅

contradict	jarvis contradict input.json \[--use-llm]	✅

zotero-sync	jarvis zotero-sync input.json	✅

pipeline	jarvis pipeline "query" --max 50 --obsidian --zotero --prisma --bibtex --no-summary	✅

browse	jarvis browse <URL> \[--json] \[--output results.json]	✅

skills	jarvis skills list|match|show|context \[--query "..."] \[--name "..."]	✅

mcp	jarvis mcp servers|tools|invoke|status \[--tool ...] \[--params-file ...]	✅

orchestrate	jarvis orchestrate agents|status|decompose|run \[--goal "..."] \[--max N]	✅

run	jarvis run --goal "..." \[--category ...]	v1から存在

(bibtex)	search/merge/pipeline の --bibtex フラグ経由	✅

6.1 pipeline コマンドの実行フロー（7ステップ）

jarvis pipeline "immunosenescence autophagy" --max 10 --obsidian --zotero --prisma --bibtex

&nbsp; ├─ Step 1/7: \_step\_search()      → UnifiedSourceClient (PubMed+OpenAlex+arXiv+Crossref)

&nbsp; ├─ Step 2/7: \_step\_dedup()       → DOI完全一致 → タイトル完全一致 → fuzzy match (>=90%)

&nbsp; ├─ Step 3/7: \_step\_evidence()    → grade\_evidence(use\_llm=False)

&nbsp; ├─ Step 4/7: \_step\_score()       → PaperScorer (citation×0.3 + evidence×0.3 + recency×0.2 + journal×0.2)

&nbsp; ├─ Step 5/7: \_step\_summarize()   → LLMClient(Gemini) で日本語要約生成 (--no-summary で省略可)

&nbsp; ├─ Step 6/7: エクスポート

&nbsp; │   ├─ JSON保存                  → logs/pipeline/<query>\_<timestamp>.json

&nbsp; │   ├─ Obsidian出力 (--obsidian) → config.yaml の vault\_path/JARVIS/Papers/

&nbsp; │   ├─ Zotero同期 (--zotero)     → Crossref metadata → pyzotero create\_items

&nbsp; │   ├─ PRISMA図 (--prisma)       → logs/pipeline/<run>\_prisma.md + .mmd

&nbsp; │   └─ BibTeX (--bibtex)         → logs/pipeline/<run>.bib

&nbsp; └─ Step 7/7: 実行ログ保存        → logs/pipeline/<query>\_<timestamp>\_log.json

6.2 orchestrate コマンドの実行フロー（5エージェント）

jarvis orchestrate run --goal "spermidine autophagy" --max 3

&nbsp; ├─ \[1/5] SearchAgent    → UnifiedSourceClient (PubMed + OpenAlex)

&nbsp; ├─ \[2/5] EvidenceAgent  → grade\_evidence (rule-based, CEBM)

&nbsp; ├─ \[3/5] ScoringAgent   → score\_papers (jarvis\_cli.score)

&nbsp; ├─ \[4/5] SummarizeAgent → Sort by quality\_score, rank top 5

&nbsp; └─ \[5/5] ReviewAgent    → abstract/DOI coverage check, duplicate detection

&nbsp; → Results: logs/orchestrate/<goal>\_<timestamp>.json

6.3 MCP Hub のツール一覧（5サーバー、15ツール）

サーバー	URL	ツール	テスト結果

pubmed	https://eutils.ncbi.nlm.nih.gov/entrez/eutils	pubmed\_search, pubmed\_fetch, pubmed\_citations	✅ pubmed\_search 動作確認済み（3 PMIDs返却）

openalex	https://api.openalex.org	openalex\_search, openalex\_work, openalex\_author, openalex\_institution	未テスト（ローカルハンドラ未実装）

semantic\_scholar	https://api.semanticscholar.org/graph/v1	s2\_search, s2\_paper, s2\_citations, s2\_references	未テスト

arxiv	http://export.arxiv.org/api	arxiv\_search, arxiv\_fetch	✅ arxiv\_search 動作確認済み（3件返却）

crossref	https://api.crossref.org	crossref\_search, crossref\_doi	✅ crossref\_search 動作確認済み（5件返却）

6.4 Skills System（9スキル）

スキル名	スコープ	トリガー

citation-analysis	global	citation, references, support, contrast

contradiction-detection	global	contradiction, conflict, inconsistent

evidence-grading	global	evidence level, grade evidence, CEBM, study quality

systematic-review	global	systematic review, literature review, PRISMA

paper-scoring	global	score, rank, quality, grade

active-learning	global	screen, screening, triage, relevant

browser-agent	global	browse, scrape, fetch, extract

evidence-module-generator	workspace	(none)

test-coverage-booster	workspace	(none)

7\. 重要な import パス一覧

Copy# Sources (C-5: arXiv/Crossref 追加済み)

from jarvis\_core.sources.unified\_source\_client import UnifiedSourceClient, SourceType

\# SourceType enum: PUBMED, SEMANTIC\_SCHOLAR, OPENALEX, ARXIV, CROSSREF

\# client.search(query="...", max\_results=20, sources=\[SourceType.PUBMED], deduplicate=True)

\# 注意: パラメータ名は "sources" (source\_types ではない)



\# Evidence (grade\_evidence のみ。classify\_evidence は存在しない)

from jarvis\_core.evidence import grade\_evidence

\# grade\_evidence(title="...", abstract="...", use\_llm=False) → EvidenceGrade



\# Paper Scoring

from jarvis\_cli.score import score\_papers

\# score\_papers(papers: list\[dict]) → list\[dict]  (quality\_score, quality\_grade 追加)



\# MCP Hub

from jarvis\_core.mcp.hub import MCPHub

\# hub = MCPHub(); hub.register\_all\_builtin\_servers(); hub.invoke\_tool\_sync("pubmed\_search", {"query": "..."})



\# Skills

from jarvis\_core.skills.engine import SkillsEngine

\# engine = SkillsEngine(); engine.list\_all\_skills(); engine.match\_skills("systematic review")



\# Browser Agent

from jarvis\_cli.browse import run\_browse

\# Scrapling Selector を使用。css\_first() は存在しない。css("selector")\[0] を使用



\# Orchestrate (jarvis\_core.agents.orchestrator は import 不可 — セクション5.1参照)

from jarvis\_cli.orchestrate import run\_orchestrate



\# LLM

from jarvis\_core.llm.llm\_utils import LLMClient, Message



\# Obsidian / Zotero / PRISMA / BibTeX

from jarvis\_cli.obsidian\_export import export\_papers\_to\_obsidian

from jarvis\_cli.zotero\_sync import \_get\_zotero\_client, \_build\_zotero\_item

from jarvis\_cli.prisma import run\_prisma

from jarvis\_cli.bibtex import save\_bibtex

Copy

8\. リモートリポジトリのファイル構成（jarvis\_cli/）

ファイル	サイズ	追加コミット	説明

\_\_init\_\_.py	12,071 B	C-4 9220dd5a	CLI エントリーポイント、20コマンド定義

\_\_main\_\_.py	106 B	v1	sys.exit(main())

bibtex.py	2,532 B	A-5	BibTeX 出力

browse.py	11,097 B	C-2 5564623e	Browser Agent (Scrapling)

citation\_stance.py	3,159 B	B-1 18941276	Citation Stance CLI

contradict.py	4,245 B	B-2 18941276	Contradiction 検出 CLI

evidence.py	4,955 B	T2-1	Evidence grading CLI

mcp.py	4,103 B	C-1 7320bbe6	MCP Hub CLI (--params-file 対応)

merge.py	3,779 B	v1	JSON マージ

note.py	6,966 B	v1	LLM ノート生成

obsidian\_export.py	7,477 B	B-5 18941276	Obsidian ノートテンプレート

orchestrate.py	8,550 B	C-4 9220dd5a	Multi-Agent Orchestrator CLI

pipeline.py	17,533 B	A-1〜A-5	7ステップ パイプライン

prisma.py	6,803 B	A-4	PRISMA ダイアグラム

score.py	4,608 B	B-3 18941276	Paper Scoring CLI

screen.py	7,718 B	B-4 18941276	Active Learning Screening CLI

search.py	9,731 B	C-5 024a1a86	統合検索 CLI

semantic\_search.py	4,029 B	T3-1	セマンティック検索 CLI

skills.py	3,648 B	C-3 cf73f002	Skills System CLI

zotero\_sync.py	10,147 B	T3-3	Zotero 同期 CLI

9\. Git コミット履歴（時系列、最新→古い）

9220dd5a  C-4: Multi-Agent Orchestrator                     ← リモート最新

7320bbe6  C-1: MCP Hub - CLI commands, local API execution, arXiv/Crossref servers

cf73f002  C-3: Skills System - CLI commands, builtin scan, 3 new skills

5564623e  C-2: Browser Agent with Scrapling parser (arXiv title/abstract fix)

f13ddbf4  C-6: pipeline \_step\_zotero collection support

c7f24014  C-6: Zotero collection support (auto-create, config.yaml integration)

024a1a86  B-6: Streamlit Dashboard + C-5: arXiv/Crossref integration

18941276  Phase B: Obsidian template (B-5), Paper Scoring (B-3), Citation Stance (B-1), Contradiction LLM (B-2), Active Learning (B-4)

5c043b02  Phase A: LLM summary (A-1), S2 retry (A-2), fuzzy dedup (A-3), PRISMA (A-4), BibTeX (A-5)

5feb8515  HANDOVER\_v3.md

b27d72b8  Fix: \_\_init\_\_.py の未コミット変更を反映

cd2b0206  Improve: evidence grading にキーワードフォールバックを追加

429e6362  Fix: zotero-sync を create\_items 方式に変更

f16fc286  T3-3: Zotero 連携

f75ef42d  Fix: semantic-search の HybridSearchResult len() エラーを修正

48873197  T3-1 + T3-2: semantic-search と contradict コマンドを新設

538d5a83  T2-2: Obsidian Vault 直接出力

88c87a95  T2-1: EnsembleClassifier を CLI に接続

dcd172a2  venv/ を Git 追跡から除外

38af0576  T1-3: セキュリティ整備

516eeac7  T1-2: UnifiedSourceClient を CLI に接続

10\. 既知の問題と回避策

\#	問題	原因	回避策

1	from jarvis\_core.agents.orchestrator import ... が失敗	agents.py（ファイル）と agents/（ディレクトリ）の共存	import しない。orchestrate.py は直接 UnifiedSourceClient 等を使用

2	Evidence grading で Ollama エラー	未起動	use\_llm=False で回避（pipeline.py 対応済み）

3	基礎研究論文が全て Level 5 / Grade F	ルールベース分類器の限界 + 被引用数0	正常動作（基礎研究に該当）。臨床試験論文なら高グレード

4	Orchestrate で全論文 Evidence unknown	PubMed abstract が空の論文が多い	OpenAlex 等 abstract 付きソースを追加すれば改善

5	S2 429 Too Many Requests	無料枠 100req/5min	A-2 で指数バックオフ実装済み

6	PowerShell で JSON がパースエラー	PS 5.1 のクォート処理	--params-file でファイル経由で渡す

7	\_\_init\_\_.py への部分挿入が不安定	文字列操作の問題	全文上書き方式のみ使用（write\_\*.py）

8	pip が venv 外にインストール	venv に pip 未設定だった	修復済み。python -m pip install を使用

9	Scrapling に css\_first() がない	API 非互換	css("selector")\[0] を使用（browse.py 対応済み）

10	PubMed browse で abstract 空、authors 重複	HTML 構造の差異	軽微、未修正（browse の arXiv/Generic は正常）

11	MCP openalex/s2 invoke 未テスト	ローカルハンドラ未実装	pubmed, arxiv, crossref のみ動作確認済み

11\. config.yaml 構造

Copyobsidian:

&nbsp; vault\_path: "C:\\\\Users\\\\kaneko yu\\\\Documents\\\\ObsidianVault"

&nbsp; papers\_folder: "JARVIS/Papers"

&nbsp; notes\_folder: "JARVIS/Notes"



zotero:

&nbsp; api\_key: ""           # .env から読み込むため空欄

&nbsp; user\_id: ""           # .env から読み込むため空欄

&nbsp; collection: "JARVIS"  # C-6で実装済み



search:

&nbsp; default\_sources: \[pubmed, semantic\_scholar, openalex]

&nbsp; max\_results: 20



llm:

&nbsp; default\_provider: gemini

&nbsp; gemini\_model: gemini-2.0-flash

&nbsp; cache\_enabled: true



evidence:

&nbsp; use\_llm: false

&nbsp; strategy: weighted\_average

12\. スモークテスト手順（新セッション開始時）

Copy# 1. 移動と仮想環境有効化

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1



\# 2. Python が venv 内か確認

python -c "import sys; print(sys.executable)"

\# → .venv\\Scripts\\python.exe が表示されること



\# 3. Git 状態確認

git status

git log --oneline -5



\# 4. CLI ヘルプ確認（20コマンド表示されること）

python -m jarvis\_cli --help



\# 5. import 確認

python -c "from jarvis\_core.sources.unified\_source\_client import UnifiedSourceClient; print('OK')"

python -c "from jarvis\_core.evidence import grade\_evidence; print('OK')"

python -c "from jarvis\_core.skills.engine import SkillsEngine; print('OK')"

python -c "from jarvis\_core.mcp.hub import MCPHub; print('OK')"



\# 6. 簡易 pipeline テスト（要約なし＝API不使用で高速）

python -m jarvis\_cli pipeline "autophagy" --max 3 --no-summary



\# 7. Skills テスト

python -m jarvis\_cli skills list



\# 8. MCP テスト

python -m jarvis\_cli mcp status



\# 9. Orchestrate テスト

python -m jarvis\_cli orchestrate agents



\# 10. Browse テスト

python -m jarvis\_cli browse https://arxiv.org/abs/2005.12402

Copy

13\. 全タスク完了後の残作業・改善候補

全 Phase（v2, A, B, C）の全タスクが完了済みのため、以下は品質改善・機能拡張の候補リストである。



13.1 軽微な修正（各1-2h）

\#	内容	詳細

1	PubMed browse の abstract 空問題	browse.py の PubMed セレクタ修正（div.abstract-content 等）

2	PubMed browse の authors 重複	同じ著者が2回表示される問題の修正

3	MCP invoke の openalex/s2 ローカルハンドラ	hub.py に \_local\_openalex\_search 等を追加

4	Orchestrate の Evidence unknown 改善	SearchAgent で OpenAlex も使用し abstract 取得率を上げる

5	agents.py / agents/ 衝突の根本解決	agents.py を agents\_legacy.py にリネーム、または agents/ に \_\_init\_\_.py を追加して統合

13.2 中規模の拡張（各3-8h）

\#	内容	詳細

1	Streamlit Dashboard の動作確認	python -m streamlit run jarvis\_core/app.py の実行と UI 確認

2	Orchestrate に LLM 要約ステップ追加	pipeline.py の \_step\_summarize() 相当を組み込み

3	Skills の execute アクション実装	現在 list/match/show/context のみ。execute でスキル定義に基づく自動実行

4	MCP ToolChain の統合テスト	複数ツールを連鎖実行（例: pubmed\_search → crossref\_doi → summarize）

5	テストカバレッジ向上	pytest の導入と主要モジュールのユニットテスト作成

14\. 実装時の絶対ルール

PowerShell から python -c "..." で複雑なコードを実行しない。必ず .py ファイルを作成して python filename.py で実行する。

jarvis\_cli/\_\_init\_\_.py は全文上書きのみ。部分挿入は過去に複数回失敗している。write\_\*.py スクリプトで全ファイルを書き出す方式を厳守。

パッケージインストールは python -m pip install。素の pip install はシステム Python 側にインストールされるリスクがある。

logs/ ディレクトリは .gitignore で除外。テストデータは新環境では再作成が必要（pipeline を1回実行すれば生成される）。

Gemini API 無料枠: 1,500 req/日、15 RPM。50論文の要約は余裕だが、連続テストで RPM 上限に注意。

Semantic Scholar 無料枠: 100 req/5min。A-2 のリトライで自動回復するが、大量検索は PubMed+OpenAlex 推奨。

jarvis\_core.agents.orchestrator は import 不可。agents.py / agents/ 衝突のため。orchestrate.py は直接モジュールを使用する。

Scrapling の css\_first() は存在しない。css("selector") でリストを取得し \[0] でアクセスする。

MCP invoke で JSON を渡すには --params-file を使用する。コマンドライン引数での JSON は PowerShell 5.1 で壊れる。

write\_\*.py スクリプトで triple-quoted string を使う場合、内部に """ が含まれないよう注意。過去に SyntaxError が発生している。

15\. 関連リポジトリ

リポジトリ	用途	状態

https://github.com/kaneko-ai/jarvis-ml-pipeline	メインリポジトリ	Phase A/B/C 全完了・プッシュ済み

https://github.com/kaneko-ai/zotero-doi-importer	Zotero DOI 登録ツール	A-6完了（.env 追跡除外、コミット 0cb2447）

16\. 用語集

用語	説明

CEBM Oxford Scale	Centre for Evidence-Based Medicine のエビデンスレベル分類（1a〜5）

RRF	Reciprocal Rank Fusion — 複数検索ランキングの統合手法

PRISMA 2020	系統的レビューの報告ガイドライン。文献選択過程をフローチャートで図示

PICO	Population, Intervention, Comparator, Outcome — 臨床研究の構造化フレームワーク

UnifiedSourceClient	PubMed/S2/OpenAlex/arXiv/Crossref を統一インターフェースで検索するクライアント

EnsembleClassifier	ルールベース + LLM の重み付け平均でエビデンスレベルを判定する分類器

MCP	Model Context Protocol — AI ツール統合プロトコル

MCPHub	複数の MCP サーバーを管理し、ツール呼び出しを仲介するハブクラス

SkillsEngine	SKILL.md ファイルからスキル定義を自動検出・パースするエンジン

Scrapling	Python の HTML パーサーライブラリ。css() で CSS セレクタ検索

rapidfuzz	文字列類似度計算ライブラリ。fuzzy dedup に使用

ActiveLearningEngine	不確実性サンプリングによる効率的文献スクリーニングエンジン

