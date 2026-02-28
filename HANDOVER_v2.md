JARVIS Research OS — 引き継ぎ書 v2（Handover Document）

作成日: 2026-02-28 最終更新日: 2026-02-28 作成者: AI アシスタント（Claude） 対象リポジトリ: https://github.com/kaneko-ai/jarvis-ml-pipeline 対象ユーザー: kaneko yu（大学院生、2026年4月 研究室配属予定）



1\. プロジェクト概要

JARVIS Research OS は、系統的文献レビュー（Systematic Literature Review）を支援するローカルファースト AI リサーチアシスタントである。PubMed・Semantic Scholar・OpenAlex・arXiv・Crossref 等の無料 API から論文を検索・収集し、LLM（Gemini / Codex GPT-5.2）による日本語要約、CEBM エビデンスレベル判定、被引用数分析、セマンティック検索、矛盾検出、PRISMA フロー図生成、研究ノート自動作成までを CLI と Streamlit ダッシュボードで一貫して実行できる。生成された研究ノートは Obsidian Vault に直接出力され、Zotero との三角連携により文献管理からナレッジ構築までをシームレスに接続する。



研究テーマ: PD-1 免疫チェックポイント阻害剤（106 論文収集済み）、スペルミジン（46 論文収集済み） 想定される配属後の研究領域: 免疫学×老化・オートファジー（免疫老化、腫瘍免疫微小環境、スペルミジンの免疫増強作用など。配属後に先輩の研究を引き継ぐ形で確定予定）



2\. アーキテクチャ図

2.1 現状版（2026-02-28 時点）

CLIで実際に動作する部分を実線、コードは存在するがCLIに未接続の部分を破線で示す。



jarvis\_core/（コード存在・CLI未接続）



外部 API（現在使用中）



LLM プロバイダー



CLI コマンド（実装済み・動作確認済み）



ユーザーインターフェース



未接続



未接続



未接続



未接続



データ



logs/search/\*.json

論文データ



logs/search/\*.bib

BibTeX



logs/notes/\*.md

研究ノート



logs/citation/\*.json

被引用数データ



logs/prisma/\*.mmd

PRISMA図



jarvis\_cli/

CLI エントリポイント



app.py

Streamlit ダッシュボード



jarvis search

論文検索 + LLM要約



jarvis merge

マージ \& 重複除去



jarvis note

研究ノート生成



jarvis citation

被引用数分析



jarvis prisma

PRISMA フロー図



jarvis bibtex

BibTeX エクスポート



llm\_utils.py

LLMClient



Gemini API

（無料枠 1500/日）



Codex CLI

（GPT-5.2）



Ollama

（ローカル）



Mock

（テスト用）



PubMed E-utilities

（jarvis\_cli/search.py 直接呼出）



Semantic Scholar API

（被引用数取得）



sources/

UnifiedSourceClient

PubMed+S2+OpenAlex統合



evidence/

EnsembleClassifier

CEBM エビデンス判定



embeddings/

HybridSearch

SentenceTransformers+BM25



contradiction/

ContradictionDetector

矛盾検出



citation/

スタンス分類



prisma/

PRISMA コアロジック



Copy

2.2 理想版（2026年4月目標 + 中長期構想）

実線は3月中に実装予定、破線は4月以降の構想を示す。



中長期構想（4月以降）



外部ツール連携



ユーザーインターフェース



分析エンジン



CEBM エビデンス判定

Rule + LLM Ensemble



セマンティック検索

BM25 + SentenceTransformers



矛盾検出

ヒューリスティック + LLM



引用スタンス分類

Support/Contrast/Mention



統合検索ソース



UnifiedSourceClient



PubMed



Semantic Scholar



OpenAlex



arXiv



Crossref



LLM プロバイダー切替



LLM Router

（プロバイダー自動選択）



Gemini API



Codex CLI

GPT-5.2



Ollama

ローカル LLM



jarvis pipeline（一気通貫）



1\. 統合検索

PubMed+S2+OpenAlex

2\. マージ

\& 重複除去

3\. LLM要約

\& エビデンス判定

4\. 被引用数分析

\& 矛盾検出

5\. 研究ノート生成

6\. Obsidian Vault

出力

jarvis\_cli/

CLI



Streamlit

ダッシュボード



Obsidian

ナレッジベース



Zotero

文献管理



Obsidian Vault

直接 .md 書込み

YAML frontmatter付与



Zotero Web API

BibTeX/RIS インポート



Zotero Integration

Obsidian プラグイン



MCP Hub

統一API呼出し



マルチエージェント

検索→スクリーニング→評価→要約



全文PDF + RAG

Unpaywall + ベクトルDB



Active Learning

不確実性サンプリング



SKILL.md

Claude Code Skills

anti-human-bottleneck



Copy

2.3 LLMプロバイダー切替フロー図

gemini



codex



ollama



mock



未指定



Yes



No



No



Yes (429)



Yes



No



Yes



No



Yes



No



LLM 呼び出し要求



--provider 指定

or LLM\_PROVIDER 環境変数



GEMINI\_API\_KEY

設定済み？



Codex CLI

インストール済み？



Ollama サーバー

起動中？



MockProvider

ダミー応答を返す



レート制限

（15 RPM）超過？



Codex にフォールバック



Gemini API 呼び出し

4秒待機挿入



40秒待機 → リトライ

3回失敗で Codex フォールバック



codex exec 実行

UTF-8 一時ファイル経由



Gemini にフォールバック



Ollama API 呼び出し

ローカル推論



\_summary\_cache

にキャッシュ済み？



キャッシュから返却



API 呼び出し → キャッシュ保存



結果を返却



Copy

2.4 データフロー図（検索→Obsidian保存の一気通貫）

4\. 保存先

3\. 出力

2\. 処理パイプライン

1\. 統合検索

入力



検索クエリ

例: PD-1 immunotherapy



config.yaml

Obsidian Vault パス

LLM 設定等



PubMed

E-utilities



Semantic

Scholar



OpenAlex



UnifiedSourceClient

→ UnifiedPaper\[]



マージ \& 重複除去

DOI/PMID/タイトル正規化



LLM 日本語要約

Gemini or Codex



CEBM エビデンス判定

Rule + LLM Ensemble



被引用数取得

Semantic Scholar API



矛盾検出

反意語 + コンテキスト類似度



論文データ JSON



BibTeX / RIS



研究ノート .md



PRISMA フロー図 .mmd



logs/ ディレクトリ



Obsidian Vault

YAML frontmatter 付き .md



Zotero ライブラリ

BibTeX/RIS インポート



Streamlit ダッシュボード



Copy

2.5 ディレクトリ構成ツリー図

jarvis-ml-pipeline/

├── jarvis\_cli/                    # CLI コマンド群（ユーザー直接操作）

│   ├── \_\_init\_\_.py                #   argparse ルーティング

│   ├── \_\_main\_\_.py                #   python -m jarvis\_cli

│   ├── search.py                  #   ★ 論文検索 + LLM 要約

│   ├── merge.py                   #   ★ マージ \& 重複除去

│   ├── note.py                    #   ★ 研究ノート生成

│   ├── citation.py                #   ★ 被引用数分析

│   ├── prisma.py                  #   ★ PRISMA フロー図

│   ├── bibtex.py                  #   ★ BibTeX エクスポート

│   ├── evidence.py                #   ☆ Week 2 で新設予定

│   ├── semantic\_search.py         #   ☆ Week 3 で新設予定

│   ├── contradict.py              #   ☆ Week 3 で新設予定

│   ├── pipeline.py                #   ☆ Week 4 で新設予定

│   └── obsidian\_export.py         #   ☆ Week 2 で新設予定

│

├── jarvis\_core/                   # コアロジック（CLI から呼び出し）

│   ├── llm\_utils.py               #   ★ LLMClient 統合

│   ├── llm\_provider.py            #   ★ プロバイダーファクトリ

│   ├── llm/                       #   ★ LLM アダプター群

│   ├── agents/                    #   △ スタブ（将来のオーケストレーション用）

│   ├── sources/                   #   ◎ UnifiedSourceClient 完成済み → Week 1 接続

│   │   ├── pubmed\_client.py       #     PubMed E-utilities クライアント

│   │   ├── semantic\_scholar\_client.py  # Semantic Scholar クライアント

│   │   ├── openalex\_client.py     #     OpenAlex クライアント

│   │   ├── unified\_source\_client.py  # ◎ 統合クライアント

│   │   └── chunking.py            #     テキストチャンキング

│   ├── evidence/                  #   ◎ EnsembleClassifier 完成済み → Week 2 接続

│   │   ├── schema.py              #     EvidenceLevel, EvidenceGrade

│   │   ├── rule\_classifier.py     #     ルールベース分類器

│   │   ├── llm\_classifier.py      #     LLM ベース分類器

│   │   ├── ensemble.py            #     ◎ アンサンブル（加重平均/投票/信頼度）

│   │   └── store.py               #     EvidenceStore

│   ├── embeddings/                #   ◎ HybridSearch 完成済み → Week 3 接続

│   │   ├── sentence\_transformer.py #    Sentence Transformers

│   │   ├── bm25.py                #     BM25 インデックス

│   │   ├── hybrid.py              #     ◎ ハイブリッド検索（RRF融合）

│   │   ├── specter2.py            #     SPECTER2（科学論文特化）

│   │   └── embedder.py            #     汎用エンベッダー

│   ├── contradiction/             #   ◎ ContradictionDetector 完成済み → Week 3 接続

│   │   ├── schema.py              #     Claim, ContradictionResult

│   │   ├── detector.py            #     ◎ 反意語ヒューリスティック検出

│   │   └── normalizer.py          #     クレーム正規化

│   ├── citation/                  #   △ スタンス分類（一部実装）

│   ├── prisma/                    #   ★ PRISMA 生成コアロジック

│   ├── api/                       #   外部 API クライアント

│   └── network/                   #   ネットワーク検出・オフラインモード

│

├── app.py                         # ★ Streamlit ダッシュボード

├── config.yaml                    # ☆ Week 2 で新設予定

├── .env                           # API キー（.gitignore 対象）

├── pyproject.toml                 # パッケージ定義

├── requirements.txt               # 依存パッケージ

│

├── logs/                          # データディレクトリ

│   ├── search/                    #   論文 JSON, Markdown, BibTeX

│   ├── notes/                     #   研究ノート Markdown

│   ├── citation/                  #   被引用数データ

│   └── prisma/                    #   PRISMA フロー図

│

├── tests/                         # テストコード

├── docs/                          # ドキュメント

└── HANDOVER\_v2.md                 # ← この文書

凡例: ★ 動作確認済み、◎ コード完成済み・CLI接続予定、☆ 新規作成予定、△ スタブ/一部実装



3\. 環境情報

項目	値

OS	Windows 11

シェル	PowerShell 5.1

Python	3.12.3

Node.js	v24.13.1

venv パス	C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\venv

Codex CLI	v0.104.0（v0.106.0 にアップデート可能）

Streamlit	1.54.0

google-genai	1.65.0

google-generativeai	0.8.6

requests	2.32.5

ライセンス	MIT

環境変数（.env または PowerShell で設定）:



変数名	用途	備考

GEMINI\_API\_KEY または GOOGLE\_API\_KEY	Gemini API 認証	無料枠: 1,500 req/日、15 RPM

LLM\_PROVIDER	デフォルト LLM プロバイダー	gemini（デフォルト）、codex、ollama、mock

CODEX\_MODEL	Codex CLI で使用するモデル	デフォルト gpt-5.2

OBSIDIAN\_VAULT\_PATH	Obsidian Vault フォルダパス	☆ Week 2 で追加予定

ZOTERO\_API\_KEY	Zotero Web API 認証	☆ Week 3 で追加予定

ZOTERO\_USER\_ID	Zotero ユーザーID	☆ Week 3 で追加予定

4\. フェーズ完了状況

4.1 完了済み（v1）

フェーズ	タスク	ステータス	備考

Phase 0	環境構築	完了	Python, venv, Git, API キー設定

Phase 0.5	バグ修正	完了	初期セットアップ時の各種エラー解消

Phase 1	search/run コマンド, BibTeX 出力	完了	jarvis search, jarvis run 動作確認済み

Phase 2	P2-1: Codex CLI 統合	完了	GPT-5.2 を LLM バックエンドとして利用可能

Phase 2	P2-2: Citation 分析	完了	Semantic Scholar API 経由で被引用数取得

Phase 2	P2-3: PRISMA フロー図	完了	Mermaid 形式で生成、ダッシュボード表示

Phase 3	P3-0: merge \& 重複除去	完了	PMID/DOI/タイトル正規化で重複排除

Phase 3	P3-1: PD-1 論文 100 件収集	完了	106 件収集（目標超過達成）

Phase 3	P3-2: スペルミジン 50 件収集	ほぼ完了	46 件収集（残 4 件は追加検索で補充可能）

Phase 3	P3-3: 研究ノート自動生成	完了	PD-1・スペルミジン両方のノート生成済み

Phase 4	Streamlit ダッシュボード	完了	論文 DB、研究ノート、統計、PRISMA 表示

4.2 v2 開発計画（2026年3月）

Week	タスク ID	タスク	推定工数	依存

1	T1-1	アーキテクチャ図 2 枚 Mermaid 作成 + 画像化	4h	なし

1	T1-2	UnifiedSourceClient を CLI に接続（jarvis search --sources）	12h	なし

1	T1-3	セキュリティ整備（.gitignore確認、APIキーローテ手順、バックアップスクリプト）	4h	なし

2	T2-1	EnsembleClassifier を CLI に接続（jarvis evidence）	10h	T1-2

2	T2-2	Obsidian Vault 直接出力（config.yaml + YAML frontmatter + jarvis note --obsidian）	12h	なし

3	T3-1	HybridSearch を CLI に接続（jarvis semantic-search）	10h	T1-2

3	T3-2	ContradictionDetector を CLI に接続（jarvis contradict）	6h	T1-2

3	T3-3	Zotero 連携（アカウント確認/作成、RIS エクスポート、Web API 同期）	8h	なし

4	T4-1	jarvis pipeline 一気通貫コマンド新設	16h	T1-2, T2-1, T2-2

4	T4-2	横展開テスト（免疫老化×オートファジーで 50 件 pipeline 実行）	6h	T4-1

4	T4-3	ダッシュボード拡張（エビデンス分布、セマンティック検索、矛盾表示）	8h	T2-1, T3-1, T3-2

4	T4-4	引き継ぎ書 v2 完成版（CLI リファレンス更新、セットアップ手順追加）	4h	全タスク

合計推定工数: 約 100h（1日4〜6時間 × 約20日で収まる想定）



5\. READMEと実態のギャップ分析

リポジトリの README に記載されている機能と、実際に CLI から使用できる機能の間にギャップが存在する。このセクションではそのギャップを明示し、v2 開発計画での対処方針を示す。



README 記載機能	jarvis\_core/ コード	CLI 接続	v2 対処

Hybrid Search (ST + BM25)	embeddings/ に完全実装	未接続	T3-1 で接続

Free APIs (arXiv, Crossref, Unpaywall)	sources/ に PubMed + S2 + OpenAlex 実装済み。arXiv/Crossref/Unpaywall は一部	未接続	T1-2 で統合検索接続

Evidence Grading (CEBM)	evidence/ に Rule + LLM + Ensemble 完全実装	未接続	T2-1 で接続

Citation Stance Analysis	citation/ に一部実装	未接続	v2 スコープ外（将来）

Contradiction Detection	contradiction/ にヒューリスティック実装	未接続	T3-2 で接続

PRISMA 2020 Diagrams	prisma/ に実装	接続済み	完了

Paper Scoring	README のみ	未実装	v2 スコープ外

Active Learning	README のみ	未実装	v2 スコープ外

MCP Hub	README のみ	未実装	v2 スコープ外（図に構想のみ反映）

Browser Agent	README のみ	未実装	v2 スコープ外

Skills System	README のみ	未実装	v2 スコープ外（設計パターンとして参考）

Multi-Agent Orchestrator	agents/ にスタブ	未実装	v2 スコープ外（jarvis pipeline で簡易版）

Zotero Integration	README のみ	未実装	T3-3 で実装

6\. CLI コマンドリファレンス

6.1 既存コマンド（動作確認済み）

Copy# 論文検索（Gemini で日本語要約付き）

python -m jarvis\_cli search "PD-1 immunotherapy" --max 20



\# Codex（GPT-5.2）で要約

python -m jarvis\_cli search "PD-1 immunotherapy" --max 20 --provider codex



\# 要約なし（高速、API 消費なし）

python -m jarvis\_cli search "PD-1 immunotherapy" --max 20 --no-summary



\# JSON + BibTeX 出力

python -m jarvis\_cli search "PD-1 immunotherapy" --max 20 --provider codex --json --bibtex



\# マージ \& 重複除去

python -m jarvis\_cli merge "logs/search/file1.json" "logs/search/file2.json" -o "logs/search/merged.json" --bibtex



\# 研究ノート生成

python -m jarvis\_cli note "logs/search/PD-1\_final.json" --provider gemini



\# 被引用数分析

python -m jarvis\_cli citation "logs/search/PD-1\_final.json"



\# PRISMA フロー図

python -m jarvis\_cli prisma "logs/search/file1.json" "logs/search/file2.json"



\# ダッシュボード起動

streamlit run app.py

6.2 新設予定コマンド（v2）

Copy# 統合検索（Week 1: PubMed + Semantic Scholar + OpenAlex）

python -m jarvis\_cli search "PD-1 immunotherapy" --max 20 --sources pubmed,s2,openalex



\# CEBM エビデンスレベル判定（Week 2）

python -m jarvis\_cli evidence "logs/search/PD-1\_final.json"

python -m jarvis\_cli evidence "logs/search/PD-1\_final.json" --use-llm   # LLM併用



\# 研究ノート → Obsidian Vault 直接出力（Week 2）

python -m jarvis\_cli note "logs/search/PD-1\_final.json" --provider gemini --obsidian



\# セマンティック検索（Week 3: 収集済みDB内を意味検索）

python -m jarvis\_cli semantic-search "immune checkpoint resistance" --db "logs/search/PD-1\_final.json"



\# 矛盾検出（Week 3）

python -m jarvis\_cli contradict "logs/search/PD-1\_final.json"



\# 一気通貫パイプライン（Week 4）

python -m jarvis\_cli pipeline "immunosenescence autophagy" --max 50 --provider gemini --obsidian



\# Zotero 同期（Week 3）

python -m jarvis\_cli zotero-sync "logs/search/PD-1\_final.json"

7\. Obsidian 連携設計

7.1 基本方針

Obsidian Vault は単なるフォルダ + Markdown ファイルであるため、Obsidian CLI（Catalyst $25 必要）は使用せず、Python から Vault フォルダに直接 .md ファイルを書き込む方式を採用する。Obsidian はフォルダ監視により自動的に新規ファイルを検知・表示する。



7.2 config.yaml の設計

Copyobsidian:

&nbsp; vault\_path: "C:\\\\Users\\\\kaneko yu\\\\Documents\\\\ObsidianVault"

&nbsp; papers\_folder: "JARVIS/Papers"

&nbsp; notes\_folder: "JARVIS/Notes"

&nbsp; templates\_folder: "JARVIS/Templates"

&nbsp; auto\_open: false  # Obsidian CLI 未使用のため false



zotero:

&nbsp; api\_key: ""       # .env から読み込み

&nbsp; user\_id: ""       # .env から読み込み

&nbsp; collection: "JARVIS"



search:

&nbsp; default\_sources:

&nbsp;   - pubmed

&nbsp;   - semantic\_scholar

&nbsp;   - openalex

&nbsp; max\_results: 20



llm:

&nbsp; default\_provider: gemini

&nbsp; gemini\_model: gemini-2.0-flash

&nbsp; cache\_enabled: true



evidence:

&nbsp; use\_llm: false     # true にすると LLM 併用（API 消費）

&nbsp; strategy: weighted\_average

7.3 Obsidian 出力フォーマット

各論文は以下の YAML frontmatter 付き Markdown として Vault に保存される。



Copy---

title: "Safety, activity, and immune correlates of anti-PD-1 antibody in cancer"

authors:

&nbsp; - Topalian SL

&nbsp; - Hodi FS

&nbsp; - Brahmer JR

year: 2012

journal: "New England Journal of Medicine"

doi: "10.1056/NEJMoa1200690"

pmid: "22658127"

citation\_count: 11751

evidence\_level: "1b"

evidence\_confidence: 0.85

tags:

&nbsp; - PD-1

&nbsp; - immunotherapy

&nbsp; - clinical-trial

&nbsp; - JARVIS

source: JARVIS Research OS

created: 2026-03-08

---



\# Safety, activity, and immune correlates of anti-PD-1 antibody in cancer



\## 基本情報

\- \*\*著者\*\*: Topalian SL, Hodi FS, Brahmer JR, ...

\- \*\*雑誌\*\*: New England Journal of Medicine (2012)

\- \*\*被引用数\*\*: 11,751

\- \*\*エビデンスレベル\*\*: 1b（個別 RCT）



\## 日本語要約

（LLM による日本語要約がここに入る）



\## アブストラクト（原文）

（PubMed から取得したアブストラクト）



\## 関連リンク

\- \[PubMed](https://pubmed.ncbi.nlm.nih.gov/22658127/)

\- \[DOI](https://doi.org/10.1056/NEJMoa1200690)

Copy

研究ノート（jarvis note の出力）は JARVIS/Notes/ フォルダに保存され、個別論文ノートへの \[\[wikilink]] を含む形で生成される。これにより Obsidian のグラフビューで論文間の関連が可視化される。



7.4 Zotero → Obsidian → JARVIS 三角連携

Zotero（文献管理）

&nbsp; │  BibTeX/RIS エクスポート

&nbsp; │  Zotero Integration プラグイン

&nbsp; ▼

Obsidian（ナレッジベース）

&nbsp; │  Vault フォルダ内の .md

&nbsp; │  YAML frontmatter でメタデータ管理

&nbsp; │  グラフビューで関連可視化

&nbsp; ▲

&nbsp; │  Python 直接書込み

&nbsp; │

JARVIS（検索・分析エンジン）

&nbsp; │  jarvis search → jarvis note --obsidian

&nbsp; │  jarvis zotero-sync（BibTeX → Zotero Web API）

&nbsp; ▼

Zotero（ライブラリに論文が追加される）

Zotero 側のセットアップ手順:



Zotero アプリを開き、アカウントにログインしているか確認する（設定 → 同期 → アカウント）。ログインしていなければ https://www.zotero.org/user/register/ でアカウントを作成する。

https://www.zotero.org/settings/keys にアクセスし、API キーを生成する。「Allow library access」にチェック。「Allow write access」にチェック。

同ページに表示される User ID をメモする。

.env に ZOTERO\_API\_KEY と ZOTERO\_USER\_ID を追加する。

Obsidian 側で Zotero Integration プラグインをインストールし、Zotero のデータディレクトリを指定する。

8\. セキュリティとデータ管理

8.1 .gitignore 確認チェックリスト

以下のファイル/フォルダが .gitignore に含まれていることを確認する。



.env

\*.key

logs/

venv/

\_\_pycache\_\_/

\*.pyc

.cache/

確認コマンド:



Copy# .env が追跡されていないことを確認

git ls-files --error-unmatch .env

\# エラーが出れば追跡されていない（正常）

8.2 API キーローテーション手順

Gemini API キー:



https://aistudio.google.com/app/apikey にアクセス

既存キーを削除（「Delete API key」）

新しいキーを生成（「Create API key」）

.env の GEMINI\_API\_KEY を新しいキーに更新

動作確認: python -m jarvis\_cli search "test" --max 1

Zotero API キー（設定後）:



https://www.zotero.org/settings/keys にアクセス

既存キーを削除し新規作成

.env の ZOTERO\_API\_KEY を更新

ローテーション推奨頻度: 3ヶ月に1回、または漏洩が疑われた場合は即時。



8.3 ローカルバックアップ戦略

以下のPowerShellスクリプトを backup.ps1 として保存し、週次で実行する。



Copy# backup.ps1 - JARVIS データバックアップ

$timestamp = Get-Date -Format "yyyyMMdd\_HHmmss"

$source = "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\logs"

$dest = "D:\\Backup\\jarvis"  # バックアップ先（別ドライブ推奨）



if (-not (Test-Path $dest)) {

&nbsp;   New-Item -ItemType Directory -Path $dest -Force

}



$zipPath = Join-Path $dest "jarvis\_logs\_$timestamp.zip"

Compress-Archive -Path $source -DestinationPath $zipPath -Force

Write-Host "Backup created: $zipPath"



\# 30日以上前のバックアップを削除

Get-ChildItem $dest -Filter "jarvis\_logs\_\*.zip" |

&nbsp;   Where-Object { $\_.LastWriteTime -lt (Get-Date).AddDays(-30) } |

&nbsp;   Remove-Item -Force

8.4 研究データの再現性ログ

各検索実行時に、以下の情報が自動記録されるよう jarvis pipeline に組み込む。



Copy{

&nbsp; "execution\_id": "pipeline\_20260315\_143022",

&nbsp; "timestamp": "2026-03-15T14:30:22+09:00",

&nbsp; "query": "immunosenescence autophagy",

&nbsp; "sources": \["pubmed", "semantic\_scholar", "openalex"],

&nbsp; "max\_results\_per\_source": 20,

&nbsp; "llm\_provider": "gemini",

&nbsp; "llm\_model": "gemini-2.0-flash",

&nbsp; "total\_retrieved": 58,

&nbsp; "after\_dedup": 45,

&nbsp; "evidence\_grading": true,

&nbsp; "obsidian\_export": true,

&nbsp; "duration\_seconds": 342

}

9\. 未実装機能の詳細分析と接続計画

9.1 UnifiedSourceClient（最優先 T1-2）

コードの現状: jarvis\_core/sources/unified\_source\_client.py に完全実装済み。PubMedClient, SemanticScholarClient, OpenAlexClient を統合し、UnifiedPaper データクラスに正規化。DOI ベースの重複排除済み。search(), get\_by\_doi(), get\_by\_pmid(), get\_citations() メソッド完備。



CLI 接続の方針: 現在の jarvis\_cli/search.py は PubMed E-utilities を直接呼び出している。これを UnifiedSourceClient 経由に切り替え、--sources オプションで検索先を指定可能にする。後方互換のため、--sources 未指定時は PubMed のみ（従来動作）とする。



実装上の注意: OpenAlex と Semantic Scholar は無料だがレート制限が異なる。OpenAlex は polite pool を使用するためメールアドレス設定を推奨。Semantic Scholar は 100 req/5min。3 ソース並列ではなく順次呼び出しとし、各ソースで失敗しても他のソースで継続する設計が UnifiedSourceClient に既に組み込まれている。



9.2 EnsembleClassifier（T2-1）

コードの現状: jarvis\_core/evidence/ensemble.py に完全実装済み。5種類のアンサンブル戦略（WEIGHTED\_AVERAGE, VOTING, CONFIDENCE\_BASED, RULE\_FIRST, LLM\_FIRST）をサポート。RuleBasedClassifier はタイトル・アブストラクトのキーワードから研究デザインを推定。LLMBasedClassifier は Gemini/Codex で判定。



CLI 接続の方針: jarvis evidence <input.json> コマンドを新設。入力 JSON の各論文に対して grade\_evidence(title, abstract) を呼び出し、結果を JSON に追記（evidence\_level, evidence\_confidence, study\_type フィールド）。まず use\_llm=False で高速に全件処理し、信頼度が低い（< 0.6）論文のみ LLM で再判定するハイブリッドフローとする。



9.3 HybridSearch（T3-1）

コードの現状: jarvis\_core/embeddings/ に Sentence Transformers（all-MiniLM-L6-v2）、BM25、RRF融合の HybridSearch、および科学論文特化の SPECTER2 が実装済み。



CLI 接続の方針: jarvis semantic-search <query> --db <input.json> コマンドを新設。初回実行時にインデックスを構築（logs/index/ に保存）、2回目以降はキャッシュ利用。結果はスコア付きで上位 N 件を返す。Sentence Transformers のモデルダウンロード（約 80MB）が初回に発生することを明記。



9.4 ContradictionDetector（T3-2）

コードの現状: jarvis\_core/contradiction/detector.py にヒューリスティック実装。反意語ペア（increase/decrease, effective/ineffective 等）とJaccard類似度の組み合わせで矛盾を検出。精度は限定的だが、明確な矛盾は捕捉可能。



CLI 接続の方針: jarvis contradict <input.json> コマンドを新設。全論文ペアのアブストラクトを比較し、矛盾スコア > 0.5 のペアをレポートとして出力。106 件では最大 5,565 ペアの比較になるが、ヒューリスティックベースなので数秒で完了する。将来的に LLM による高精度矛盾検出に拡張可能。



10\. 外部ツール連携の設計パターン参考

10.1 Claude Code Skills の anti-human-bottleneck パターン

逆瀬川氏の記事（https://nyosegawa.github.io/posts/claude-code-verify-command/）から得られた知見。Claude Code Skills に「人間に質問する前にロードされるメタスキル」を定義することで、エージェントの自律動作を実現するパターンである。



JARVIS への適用可能性: 将来のマルチエージェントパイプライン（jarvis\_core/agents/）を構築する際、各エージェント（検索エージェント、スクリーニングエージェント、評価エージェント）が自律的にタスクを進行し、人間の介入を最小化する設計に活用できる。具体的には、jarvis pipeline コマンドが途中で人間に確認を求めず、各ステップの結果をログに記録しながら最後まで自動実行するという現時点の設計方針と合致する。



10.2 OpenClaw ACP（Agent Client Protocol）

外部コーディングエージェント（Claude Code, Codex, Gemini CLI）をセッション管理付きで呼び出すプロトコル（https://docs.openclaw.ai/tools/acp-agents）。JARVISの文脈では、将来的に MCP Hub や マルチエージェントオーケストレーションを実装する際の設計パターンとして参照する。現時点では Discord 前提のツールであるため直接採用はしないが、セッション管理、エージェント切替、スレッドバインディングの概念は JARVIS の agents/ パッケージ設計に取り入れる価値がある。



10.3 要件定義のベストプラクティス

classmethod 記事（https://dev.classmethod.jp/articles/requirements-definition-tips-with-examples/）の主要原則を JARVIS の発展計画に適用した。



適用した原則: 「ゴールからの逆算」→ 4月配属時の理想状態を定義してからタスクを逆算。「やらないことも決める」→ v2 スコープ外を明示（MCP, Browser Agent, Active Learning 等）。「要件の量と深さはプロジェクト規模に合わせる」→ 1人で1ヶ月、1日4-6時間という制約に合わせた100h計画。「妄想を働かせる」→ 理想版アーキテクチャ図で中長期の構想を可視化。



11\. API 制限と回避策

API	制限	回避策

Gemini API（Google 無料枠）	1,500 req/日、15 RPM、リセット 00:00 PT	4秒待機、429エラー時40秒リトライ、キャッシュ、Codex併用

Codex CLI（ChatGPT Plus $20/月）	45〜225 msg/5時間（変動）	Gemini と分散、時間を空けてリトライ

Semantic Scholar API（無料）	100 req/5分（認証なし）	3.5秒間隔、429エラー時10秒リトライ

PubMed E-utilities（無料）	3 req/秒（APIキーなし）、10 req/秒（キーあり）	0.34秒間隔

OpenAlex API（無料）	polite pool: メール設定で優先	email パラメータ設定推奨

Zotero Web API（無料）	明確な制限なし、常識的な利用	バッチ処理で一括送信

12\. 収集済みデータの統計

12.1 PD-1 論文（106 件）

指標	値

総論文数	106

重複除去前	120（6 回の検索から）

除去された重複	14

アブストラクトなし	3

日本語要約なし	4

PRISMA 最終採択	99

被引用数取得成功	106/106（100%）

最多被引用	11,751（"Safety, activity, and immune correlates of anti-PD-1 antibody…", 2012）

使用した検索クエリ（6 種）: "PD-1 immunotherapy", "PD-1 checkpoint inhibitor resistance", "anti-PD-1 cancer clinical trial", "PD-1 resistance mechanism tumor", "PD-1 combination therapy efficacy", "PD-L1 expression biomarker immunotherapy"



12.2 スペルミジン論文（46 件）

指標	値

総論文数	46

被引用数取得成功	45/46（97.8%）

最多被引用	2,049（"Autophagy and aging", 2011）

使用した検索クエリ（3 種）: "spermidine autophagy", "spermidine longevity aging", "spermidine immune regulation"



13\. 既知の問題とワークアラウンド

13.1 アクティブな問題

問題	影響度	回避策

run\_qa\_gate スタブ未実装	低	無視して問題なし

EvidenceStore 未登録	低	影響なし

Codex CLI レート制限超過（>80件で発生）	中	Gemini に切替、または時間を空けてリトライ

スペルミジン残 4 件	低	追加検索 --max 5 で補充可能

jarvis\_core/agents/ がスタブ	中	v2 で jarvis pipeline により簡易オーケストレーション実装

README と実態のギャップ	中	セクション 5 で詳細分析済み、v2 で段階的に解消

13.2 解決済み問題

問題	解決方法

Windows cp932 エンコードエラー	\_chat\_codex を一時ファイル経由に変更

Gemini 429 レート制限	4 秒待機 + 40 秒リトライ + キャッシュ

Semantic Scholar references が None	or \[] で安全にフォールバック

PowerShell 5.1 互換性	リダイレクト不使用、複雑ワンライナー不使用

13.3 PowerShell 5.1 制約（必ず守ること）

python -c "..." の中で複雑なロジックを書かない（スクリプトファイルを作成する）。> リダイレクトを使わない（UTF-16 で書き込まれ Python が読めなくなる）。type \*.bib などワイルドカード展開が不安定（ファイル名を明示的に指定する）。ファイル編集は notepad <ファイル名> で行う。



14\. 今後の発展方針

14.1 v2 スコープ内（2026年3月、100h）

セクション 4.2 の Week 1〜4 タスク一覧を参照。



14.2 v2 スコープ外・中期（2026年4月〜9月）

引用ネットワーク可視化（NetworkX + Pyvis）。全文 PDF ダウンロード + RAG（Unpaywall + Sentence Transformers ベクトル化）。PRISMA 2020 完全準拠（27 項目チェックリスト + SVG/PDF エクスポート）。LLM ベース矛盾検出の高精度版。Citation Stance Analysis の CLI 接続。



14.3 v2 スコープ外・長期（2026年10月以降）

MCP Hub 実装（PubMed・Semantic Scholar・OpenAlex の統一プロトコル）。マルチエージェントパイプライン（Ralph loop パターン + anti-human-bottleneck Skills 適用）。Active Learning による効率的スクリーニング。メタ分析支援（効果量集約・フォレストプロット生成）。Obsidian Headless Sync による複数デバイス対応（Obsidian Sync サブスクリプション $4/月〜 が必要）。



15\. 開発を再開するための手順

Copy# 1. プロジェクトディレクトリに移動

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"



\# 2. venv 有効化

\& ".\\venv\\Scripts\\Activate.ps1"



\# 3. 動作確認

python -c "import jarvis\_cli; import jarvis\_core; print('OK')"



\# 4. Codex CLI 確認（ChatGPT Plus 要サインイン）

codex --version



\# 5. ダッシュボード起動で全体動作確認

streamlit run app.py



\# 6. Git 最新状態確認

git log --oneline -5

git status



\# 7. jarvis\_core モジュールのインポート確認

python -c "from jarvis\_core.sources import UnifiedSourceClient; print('Sources OK')"

python -c "from jarvis\_core.evidence import grade\_evidence; print('Evidence OK')"

python -c "from jarvis\_core.embeddings import HybridSearch; print('Embeddings OK')"

python -c "from jarvis\_core.contradiction import ContradictionDetector; print('Contradiction OK')"

16\. 技術的決定事項の記録

なぜ Codex CLI を採用したか: Gemini 無料枠（1,500 req/日、15 RPM）では 100 件規模の論文要約に数日かかる。ChatGPT Plus（$20/月）に含まれる Codex CLI を使えば、codex exec 経由で GPT-5.2 を呼び出せ、API キー不要で高品質な日本語要約が可能。



なぜ subprocess + 一時ファイル方式か: Windows の subprocess パイプはデフォルトで cp932 エンコーディングを使用するため、Codex CLI の UTF-8 出力でデコードエラーが発生する。一時ファイル（UTF-8 明示指定）で入出力を行うことで完全に回避。



なぜ Obsidian Vault 直接書込み方式か: Obsidian CLI は Catalyst ライセンス（$25）が必要な Early Access 段階であり、採用しない。Obsidian は Vault フォルダ内の .md ファイルを自動監視するため、Python から直接書き込むだけで即座に反映される。YAML frontmatter でメタデータを埋め込むことで、Obsidian のプロパティ機能・Dataview プラグイン・グラフビューと完全互換になる。



なぜ UnifiedSourceClient を CLI の検索基盤にするか: 現在の jarvis\_cli/search.py は PubMed E-utilities を直接呼び出しているが、jarvis\_core/sources/ には PubMed + Semantic Scholar + OpenAlex の統合クライアントが完成済みである。これに切り替えることで、1回の検索で3ソースを横断でき、DOI ベースの重複排除も自動化される。後方互換のため --sources pubmed のみ指定すれば従来動作と同じになる。



なぜエビデンス判定を Rule-first + LLM-fallback にするか: ルールベース分類器は API 消費ゼロ・即座に実行可能で、RCT やメタ分析は高精度に検出できる。信頼度が低い論文のみ LLM で再判定することで、API コストと精度のバランスをとる。



なぜ jarvis pipeline を Ralph loop 的に設計するか: 逆瀬川氏の記事にある通り、エージェントワークフローのボトルネックは人間の確認待ちである。jarvis pipeline は各ステップの進捗を JSON ログに記録しながら最後まで自動実行し、途中失敗時もログから再開可能にする。人間は最終結果のみレビューすればよい。



なぜ Zotero → Obsidian → JARVIS の三角連携か: Zotero は文献の書誌情報と PDF を管理する業界標準ツール、Obsidian は Markdown ベースの知識管理ツール、JARVIS は検索・分析エンジンである。三者を連携させることで、「発見 → 管理 → 分析 → 知識化」のサイクルが閉じる。Zotero Integration プラグインが Zotero-Obsidian 間を橋渡しし、JARVIS が Obsidian Vault に直接出力することで JARVIS-Obsidian 間を接続する。



17\. クイックリファレンスカード

┌──────────────────────────────────────────────────────────────────┐

│  JARVIS Research OS v2 — Quick Reference                         │

├──────────────────────────────────────────────────────────────────┤

│  検索      : jarvis search "query" --max 20 --provider codex     │

│  統合検索  : jarvis search "query" --sources pubmed,s2,openalex  │

│  マージ    : jarvis merge f1.json f2.json -o merged.json         │

│  ノート    : jarvis note merged.json --provider gemini           │

│  ノート+Obs: jarvis note merged.json --obsidian                  │

│  引用分析  : jarvis citation merged.json                         │

│  エビデンス: jarvis evidence merged.json                         │

│  意味検索  : jarvis semantic-search "query" --db merged.json     │

│  矛盾検出  : jarvis contradict merged.json                      │

│  PRISMA    : jarvis prisma f1.json f2.json                       │

│  一気通貫  : jarvis pipeline "query" --max 50 --obsidian         │

│  Zotero同期: jarvis zotero-sync merged.json                      │

│  ダッシュ  : streamlit run app.py                                │

├──────────────────────────────────────────────────────────────────┤

│  PD-1 データ        : logs/search/PD-1\_final.json (106件)        │

│  スペルミジンデータ : logs/search/spermidine\_final.json (46件)    │

│  研究ノート         : logs/notes/\*\_note.md                       │

│  被引用データ       : logs/citation/\*\_cited.json                 │

│  PRISMA 図          : logs/prisma/prisma\_\*.md                    │

│  Obsidian Vault     : config.yaml の obsidian.vault\_path         │

├──────────────────────────────────────────────────────────────────┤

│  Gemini 制限 : 1500 req/日, 15 RPM                               │

│  Codex 制限  : 45-225 msg/5h (ChatGPT Plus)                      │

│  S2 API 制限 : 100 req/5min (3.5s間隔で遵守)                     │

│  OpenAlex    : polite pool (メール設定推奨)                       │

│  PubMed      : 3 req/s (APIキーなし)                              │

├──────────────────────────────────────────────────────────────────┤

│  v2 Week 1 (3/1-7)  : 統合検索接続 + アーキテクチャ図 + セキュリティ │

│  v2 Week 2 (3/8-14) : エビデンス判定 + Obsidian連携               │

│  v2 Week 3 (3/15-21): 意味検索 + 矛盾検出 + Zotero               │

│  v2 Week 4 (3/22-31): pipeline一気通貫 + 横展開テスト + 仕上げ    │

└──────────────────────────────────────────────────────────────────┘

18\. Git コミット履歴（主要）と v2 コミット規約

18.1 既存コミット

222df2d1 feat: P2-3 PRISMA flow diagram + dashboard integration

14863b42 feat: P4-1 Streamlit dashboard with search, filter, notes, stats

38f9dc9f feat: P3-3 research note generation, complete Phase 3

b12dd4e3 feat: P3-1 PD-1 106 papers, P3-2 spermidine 46 papers collected

xxxxxxxx feat: add Codex CLI provider (GPT-5.2), merge command, --provider option

18.2 v2 コミット規約

feat: T1-2 connect UnifiedSourceClient to CLI search

feat: T2-1 add jarvis evidence command with CEBM ensemble

feat: T2-2 Obsidian Vault direct export with YAML frontmatter

feat: T3-1 add jarvis semantic-search command

feat: T3-2 add jarvis contradict command

feat: T3-3 Zotero Web API sync + RIS export

feat: T4-1 jarvis pipeline one-shot command

docs: T1-1 architecture diagrams (current + ideal)

chore: T1-3 security hardening (.gitignore, backup script)

19\. 依存パッケージ（主要 + v2 追加予定）

パッケージ	バージョン	用途	v2 追加

google-genai	1.65.0	Gemini API クライアント	

google-generativeai	0.8.6	Gemini API（レガシー互換）	

requests	2.32.5	HTTP リクエスト	

streamlit	1.54.0	Web ダッシュボード	

@openai/codex (npm)	0.104.0+	Codex CLI	

sentence-transformers	-	セマンティック検索	☆ T3-1 で使用

rank-bm25	-	BM25 検索	☆ T3-1 で使用

pyzotero	-	Zotero Web API	☆ T3-3 で使用

pyyaml	-	config.yaml 読込	☆ T2-2 で使用

defusedxml	-	安全な XML パース（PubMedClient内で使用済み）

