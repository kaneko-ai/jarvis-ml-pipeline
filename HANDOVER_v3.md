\# HANDOVER\_v3.md — JARVIS Research OS 引き継ぎ書 v3



> \*\*作成日\*\*: 2026-03-02  

> \*\*対象リポジトリ\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline  

> \*\*ブランチ\*\*: main（最終コミット: b27d72b8）  

> \*\*本書の目的\*\*: この文書を読んだ AI または開発者が、環境構築から残タスクの実装まで、追加の質問なしに 100% 再現・継続できることを保証する。



---



\## 1. プロジェクト概要



JARVIS Research OS は、系統的文献レビュー（Systematic Literature Review）を自動化するローカルファースト AI アシスタントである。CLI コマンド 1 つで「論文検索 → 重複除去 → エビデンス判定 → Obsidian ノート作成 → Zotero 登録」を一括実行できる。



\*\*主な利用者\*\*: 大学院生（プログラミング初学者）  

\*\*主な用途\*\*: PD-1 免疫療法、スペルミジン、免疫老化・オートファジーなどの研究テーマに関する文献調査



---



\## 2. 開発環境（実機ステータス）



| 項目 | 値 |

|---|---|

| OS | Windows 11 |

| シェル | PowerShell 5.1 |

| Python | 3.12.3 |

| Node.js | v24.13.1 |

| プロジェクトパス | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| venv パス | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\venv` |

| Obsidian Vault | `C:\\Users\\kaneko yu\\Documents\\ObsidianVault` |

| Obsidian 元パス（iCloud） | `C:\\Users\\kaneko yu\\iCloudDrive\\iCloud~md~obsidian\\記憶`（使用停止、ローカルに移行済み） |



\### 2.1 環境変数（.env）



`.env` はプロジェクトルートに存在し、\*\*Git 追跡外\*\*（.gitignore で除外済み）。



```

GEMINI\_API\_KEY=<Gemini APIキー>

LLM\_PROVIDER=gemini

ZOTERO\_API\_KEY=<2026-03-02に新規発行済み>

ZOTERO\_USER\_ID=16956010

```



\*\*注意\*\*: `ZOTERO\_API\_KEY` は 2026-03-02 に再発行済み。旧キーは `zotero-doi-importer` リポジトリに公開され無効化されている（セキュリティタスク #18 参照）。



\### 2.2 インストール済み主要パッケージ



```

jarvis-research-os==1.0.0（pip install -e . でインストール）

rank-bm25==0.2.2

sentence-transformers（all-MiniLM-L6-v2 モデル自動DL済み）

pyzotero

python-dotenv==1.2.1

google-genai==1.65.0

requests==2.32.5

streamlit==1.54.0

```



\### 2.3 未インストール・接続不可のコンポーネント



| コンポーネント | 状態 | 備考 |

|---|---|---|

| Ollama（ローカルLLM） | 未起動・未インストール | Evidence grading の LLM 分類器が接続試行して 127.0.0.1:11434 エラーを出す。`use\_llm=False` で回避中 |

| pandas 3.0.0 | インストール失敗（接続リセット） | 現在の機能では不要 |

| Semantic Scholar API | 429 レートリミット頻発 | 無料枠 100req/5min。リトライ機構未実装 |



---



\## 3. リポジトリ構造（主要ファイルのみ）



```

jarvis-ml-pipeline/

├── .env                          # APIキー（Git追跡外）

├── .gitignore                    # v2で強化済み（.env, logs/, venv/, \*.key, .cache/）

├── config.yaml                   # Obsidian/Zotero/LLM設定

├── backup.ps1                    # 週次バックアップスクリプト

├── app.py                        # Streamlit ダッシュボード

├── pyproject.toml                # パッケージ定義

├── HANDOVER\_v3.md                # ★ 本文書

│

├── jarvis\_cli/                   # CLI コマンド群

│   ├── \_\_init\_\_.py               # argparse定義 + ディスパッチ（全12コマンド登録済み）

│   ├── \_\_main\_\_.py               # python -m jarvis\_cli エントリポイント

│   ├── search.py                 # 論文検索（PubMed/S2/OpenAlex対応）

│   ├── merge.py                  # JSON結合＋重複除去

│   ├── note.py                   # 研究ノート生成（LLM要約）

│   ├── citation.py               # 被引用数取得

│   ├── prisma.py                 # PRISMA 2020フローチャート生成

│   ├── bibtex.py                 # BibTeX変換

│   ├── evidence.py               # ★v2: CEBM エビデンスレベル判定

│   ├── obsidian\_export.py        # ★v2: Obsidian Vault出力

│   ├── semantic\_search.py        # ★v2: ハイブリッド検索（BM25+Vector）

│   ├── contradict.py             # ★v2: 矛盾検出

│   ├── zotero\_sync.py            # ★v2: Zotero同期（pyzotero create\_items方式）

│   └── pipeline.py               # ★v2: 全工程一括実行

│

├── jarvis\_core/                  # コアロジック

│   ├── sources/                  # API クライアント群

│   │   ├── pubmed.py             # PubMedClient（NCBI E-utilities）

│   │   ├── semantic\_scholar.py   # SemanticScholarClient（S2 API）

│   │   ├── openalex.py           # OpenAlexClient（OpenAlex API）

│   │   ├── unified\_source\_client.py  # UnifiedSourceClient + SourceType enum

│   │   ├── arxiv\_client.py       # arXiv（CLI未接続）

│   │   └── crossref\_client.py    # Crossref（CLI未接続）

│   ├── evidence/                 # エビデンス判定

│   │   ├── schema.py             # EvidenceLevel, StudyType, EvidenceGrade

│   │   ├── rule\_based.py         # ルールベース分類器

│   │   ├── llm\_classifier.py     # LLM分類器（Ollama依存）

│   │   └── ensemble.py           # EnsembleClassifier + grade\_evidence()

│   ├── embeddings/               # 埋め込み・検索

│   │   ├── sentence\_transformer.py  # SentenceTransformerEmbedding

│   │   ├── bm25.py               # BM25Index

│   │   ├── hybrid.py             # HybridSearch（RRF/Linear fusion）

│   │   └── specter2.py           # SPECTER2Embedding（科学論文用）

│   ├── contradiction/            # 矛盾検出モジュール

│   ├── citation/                 # 引用分析モジュール

│   ├── prisma/                   # PRISMA図生成モジュール

│   ├── paper\_scoring/            # 論文スコアリング（雛形のみ）

│   ├── active\_learning/          # アクティブラーニング（雛形のみ）

│   ├── llm/                      # LLMユーティリティ

│   └── browser/                  # ブラウザエージェント（雛形のみ）

│

├── docs/

│   └── KEY\_MANAGEMENT.md         # APIキー管理ガイド

│

└── logs/                         # 実行ログ（Git追跡外）

&nbsp;   ├── search/                   # jarvis search の出力

&nbsp;   ├── pipeline/                 # jarvis pipeline の出力

&nbsp;   ├── notes/                    # jarvis note の出力

&nbsp;   ├── citation/                 # jarvis citation の出力

&nbsp;   └── prisma/                   # jarvis prisma の出力

```



---



\## 4. 実装済み CLI コマンド一覧



| コマンド | 使用例 | 状態 | 備考 |

|---|---|---|---|

| `search` | `jarvis search "PD-1" --max 5 --sources pubmed,s2,openalex` | 動作確認済 | S2は429エラー頻発 |

| `merge` | `jarvis merge file1.json file2.json -o merged.json` | v1から存在 | |

| `note` | `jarvis note input.json --provider gemini --obsidian` | v1から存在 | --obsidian は v2追加 |

| `citation` | `jarvis citation input.json` | v1から存在 | |

| `prisma` | `jarvis prisma file1.json file2.json -o prisma.svg` | v1から存在 | |

| `bibtex` | search/merge の `--bibtex` フラグ経由 | v1から存在 | |

| `evidence` | `jarvis evidence input.json \[--use-llm]` | \*\*v2新設\*\* | use-llm はOllama必須 |

| `obsidian-export` | `jarvis obsidian-export input.json` | \*\*v2新設\*\* | config.yaml参照 |

| `semantic-search` | `jarvis semantic-search "query" --db file.json --top 10` | \*\*v2新設\*\* | 初回14秒（モデルDL） |

| `contradict` | `jarvis contradict input.json` | \*\*v2新設\*\* | テストデータでは0件検出 |

| `zotero-sync` | `jarvis zotero-sync input.json` | \*\*v2新設\*\* | create\_items方式 |

| `pipeline` | `jarvis pipeline "query" --max 50 --obsidian --zotero` | \*\*v2新設\*\* | 全工程一括 |



\### 4.1 pipeline コマンドの実行フロー



```

jarvis pipeline "immunosenescence autophagy" --max 10 --obsidian --zotero

&nbsp; │

&nbsp; ├─ Step 1: \_step\_search()     → UnifiedSourceClient (PubMed+OpenAlex)

&nbsp; │                                フォールバック: PubMedClient のみ

&nbsp; ├─ Step 2: \_step\_dedup()      → DOI/タイトル完全一致で重複除去

&nbsp; ├─ Step 3: \_step\_evidence()   → grade\_evidence(use\_llm=False) + \_fallback\_classify()

&nbsp; ├─ Step 4: JSON保存           → logs/pipeline/<query>\_<timestamp>.json

&nbsp; │   ├─ Obsidian出力           → config.yaml の vault\_path/JARVIS/Papers/

&nbsp; │   └─ Zotero同期             → Crossref metadata → pyzotero create\_items

&nbsp; └─ Step 5: 実行ログ保存       → logs/pipeline/<query>\_<timestamp>\_log.json

```



---



\## 5. 既知の問題と回避策



| # | 問題 | 原因 | 現在の回避策 |

|---|---|---|---|

| 1 | Evidence grading で Ollama エラーが大量出力 | Ollama 未起動（127.0.0.1:11434 接続拒否） | `use\_llm=False` で回避。pipeline.py は既に対応済み |

| 2 | 基礎研究論文の evidence が全て Level 5 / unknown | ルールベース分類器は「RCT」「meta-analysis」等の明示的キーワードが必要。基礎研究は該当しない | `\_fallback\_classify()` でキーワード拡張済み（in vitro, mouse model 等→Level 5） |

| 3 | Semantic Scholar 429 Too Many Requests | 無料枠 100req/5min のレートリミット | 現状はタイムアウト→0件返却。PubMed+OpenAlex がフォールバック |

| 4 | PowerShell での Python コード直接実行がエラー | `e.g.`、f-string の `{}`、`:`等が PowerShell のコマンドとして解釈される | 別途 `.py` ファイルを作成して `python filename.py` で実行する方法に変更 |

| 5 | pyzotero に `create\_items\_from\_dois` メソッドが無い | pyzotero の新バージョンでは廃止 | `create\_items` + `item\_template("journalArticle")` + Crossref メタデータ取得で代替実装済み |

| 6 | `\_\_init\_\_.py` への自動挿入が繰り返し失敗 | write スクリプトの文字列操作が不安定 | `fix\_init.py` で全文上書き方式に変更して解決。今後も全文上書き推奨 |



---



\## 6. 重要な import パス一覧



```python

\# Sources

from jarvis\_core.sources import UnifiedSourceClient

from jarvis\_core.sources.unified\_source\_client import SourceType

from jarvis\_core.sources import PubMedClient, SemanticScholarClient, OpenAlexClient



\# Evidence

from jarvis\_core.evidence import grade\_evidence

\# grade\_evidence(title="...", abstract="...", use\_llm=False) → EvidenceGrade

\# EvidenceGrade.level.value → "1a", "1b", "2b", "3b", "4", "5", "unknown"

\# EvidenceGrade.study\_type.value → "randomized\_controlled\_trial", etc.

\# EvidenceGrade.confidence → 0.0〜1.0



\# Embeddings / Hybrid Search

from jarvis\_core.embeddings import HybridSearch

\# HybridSearch.search() → HybridSearchResult（.results がリスト、len() は .results に対して使う）



\# Obsidian export

from jarvis\_cli.obsidian\_export import export\_papers\_to\_obsidian



\# Zotero

from jarvis\_cli.zotero\_sync import \_get\_zotero\_client, \_build\_zotero\_item, \_get\_crossref\_metadata

```



---



\## 7. config.yaml 構造



```yaml

obsidian:

&nbsp; vault\_path: "C:\\\\Users\\\\kaneko yu\\\\Documents\\\\ObsidianVault"

&nbsp; papers\_folder: "JARVIS/Papers"

&nbsp; notes\_folder: "JARVIS/Notes"



zotero:

&nbsp; api\_key: ""           # .env から読み込むため空欄

&nbsp; user\_id: ""           # .env から読み込むため空欄

&nbsp; collection: "JARVIS"  # 未実装：特定コレクションへの振り分け



search:

&nbsp; default\_sources: \[pubmed, semantic\_scholar, openalex]

&nbsp; max\_results: 20



llm:

&nbsp; default\_provider: gemini

&nbsp; gemini\_model: gemini-2.0-flash

&nbsp; cache\_enabled: true



evidence:

&nbsp; use\_llm: false            # true にするには Ollama 起動が必要

&nbsp; strategy: weighted\_average

```



---



\## 8. Git コミット履歴（v2 実装分）



```

b27d72b8  Fix: \_\_init\_\_.py の未コミット変更を反映

cd2b0206  Improve: evidence grading にキーワードフォールバックを追加

429e6362  Fix: zotero-sync を create\_items 方式に変更 + コマンド登録修正

f16fc286  T3-3: Zotero 連携 (zotero-sync コマンド, pyzotero使用)

f75ef42d  Fix: semantic-search の HybridSearchResult len() エラーを修正

48873197  T3-1 + T3-2: semantic-search と contradict コマンドを新設

538d5a83  T2-2: Obsidian Vault 直接出力 (config.yaml + obsidian-export コマンド)

88c87a95  T2-1: EnsembleClassifier を CLI に接続 (jarvis evidence コマンド新設)

dcd172a2  venv/ を Git 追跡から除外

38af0576  T1-3: セキュリティ整備 (.gitignore強化, backup.ps1, KEY\_MANAGEMENT.md)

516eeac7  T1-2: UnifiedSourceClient を CLI に接続 (--sources オプション追加)

```



---



\## 9. 動作確認コマンド（環境セットアップ後のスモークテスト）



以下を順に実行し、全て成功することを確認する。



```powershell

\# 1. venv 有効化

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\venv\\Scripts\\Activate.ps1



\# 2. CLI ヘルプ確認（12コマンドが表示される）

python -m jarvis\_cli --help



\# 3. PubMed 検索

python -m jarvis\_cli search "PD-1 immunotherapy" --max 3 --no-summary



\# 4. マルチソース検索

python -m jarvis\_cli search "PD-1 immunotherapy" --max 3 --sources pubmed,openalex --no-summary



\# 5. Evidence grading

python -m jarvis\_cli evidence "logs/search/test\_evidence.json"



\# 6. Obsidian export

python -m jarvis\_cli obsidian-export "logs/search/test\_evidence\_evidence.json"



\# 7. Pipeline（小規模）

python -m jarvis\_cli pipeline "autophagy" --max 3



\# 8. Pipeline（フル）

python -m jarvis\_cli pipeline "PD-1 immunotherapy" --max 5 --obsidian --zotero



\# 9. import パス確認

python -c "from jarvis\_core.sources import UnifiedSourceClient; print('OK')"

python -c "from jarvis\_core.evidence import grade\_evidence; print('OK')"

python -c "from jarvis\_core.embeddings import HybridSearch; print('OK')"

```



---



\## 10. 残タスク一覧（v3 ロードマップ）



\### Phase A: 高優先度（実用性に直結）— 推定 15h



\#### A-1: LLM 要約の pipeline 統合（4h）



\*\*目的\*\*: pipeline 実行時に Gemini API で各論文の日本語要約を生成し、Obsidian ノートに含める。



\*\*現状\*\*: `jarvis\_cli/search.py` の `run\_search()` 内に LLM 要約ロジックが存在する（`LLMClient` を使用）。`pipeline.py` にはこのステップが無い。



\*\*実装方針\*\*:

1\. `pipeline.py` に `\_step\_summarize(papers, provider)` を追加。

2\. `jarvis\_core/llm/` の `LLMClient` を使い、各論文の `title` + `abstract` から日本語要約を生成。

3\. 結果を `paper\["summary\_ja"]` に格納。

4\. `obsidian\_export.py` の `export\_single\_paper()` でフロントマターまたは本文に `summary\_ja` を出力。

5\. `pipeline` コマンドに `--no-summary` フラグを追加（デフォルトは要約あり）。



\*\*依存\*\*: `GEMINI\_API\_KEY` が `.env` に設定済みであること。



\*\*検証コマンド\*\*:

```powershell

python -m jarvis\_cli pipeline "PD-1 immunotherapy" --max 3 --obsidian

\# → Obsidian ノートに「## 日本語要約」セクションが含まれることを確認

```



\#### A-2: Semantic Scholar 429 対策（2h）



\*\*目的\*\*: S2 API のレートリミットに対し、指数バックオフ付きリトライを実装。



\*\*現状\*\*: `jarvis\_core/sources/semantic\_scholar.py` の `SemanticScholarClient` にはデフォルト 3 秒の `rate\_limit\_wait` があるが、429 応答時のリトライロジックが無い。



\*\*実装方針\*\*:

1\. `semantic\_scholar.py` の `\_make\_request()` メソッド内で、レスポンスが 429 の場合に `time.sleep(wait)` + 最大 3 回リトライ（wait = 5, 10, 30 秒）。

2\. リトライ超過時は空リストを返す（現状と同じ）。



\*\*検証コマンド\*\*:

```powershell

python -m jarvis\_cli search "spermidine autophagy" --max 5 --sources s2 --no-summary

\# → 429 エラーではなく、リトライ後に結果が返ることを確認

```



\#### A-3: 重複除去の精度向上（3h）



\*\*目的\*\*: タイトルの fuzzy match（類似度 90% 以上で同一判定）を追加。



\*\*現状\*\*: `pipeline.py` の `\_step\_dedup()` は DOI 完全一致 + タイトル完全一致（小文字化）のみ。



\*\*実装方針\*\*:

1\. `pip install rapidfuzz` を追加。

2\. `\_step\_dedup()` でタイトル比較に `rapidfuzz.fuzz.ratio()` を使用し、閾値 90 以上を同一と判定。

3\. DOI 一致 → タイトル完全一致 → タイトル fuzzy match の 3 段階で判定。



\#### A-4: PRISMA ダイアグラムの pipeline 統合（2h）



\*\*目的\*\*: `pipeline` 実行後に自動で PRISMA 2020 フローチャートを生成。



\*\*現状\*\*: `jarvis\_cli/prisma.py` に `run\_prisma()` が実装済み。pipeline からは呼ばれていない。



\*\*実装方針\*\*:

1\. `pipeline.py` に `\_step\_prisma()` を追加。

2\. `--prisma` フラグを pipeline コマンドに追加。

3\. 検索結果の JSON を `run\_prisma()` に渡し、SVG を `logs/pipeline/` に保存。



\#### A-5: BibTeX の pipeline 統合（1h）



\*\*目的\*\*: `--bibtex` フラグで pipeline 結果を .bib ファイルとしても保存。



\*\*現状\*\*: `jarvis\_cli/bibtex.py` に `papers\_to\_bibtex()`, `save\_bibtex()` が実装済み。



\*\*実装方針\*\*:

1\. `pipeline` コマンドに `--bibtex` フラグを追加。

2\. Step 4 で `save\_bibtex(papers, path)` を呼び出し。



\#### A-6: セキュリティ — zotero-doi-importer の .env 削除（緊急）



\*\*目的\*\*: https://github.com/kaneko-ai/zotero-doi-importer/blob/main/.env に API キーが公開されている。



\*\*対応手順\*\*:

1\. https://github.com/kaneko-ai/zotero-doi-importer にアクセス。

2\. `.env` ファイルを削除するコミットを作成。

3\. `.gitignore` に `.env` を追加。

4\. キーは 2026-03-02 に既にローテーション済みだが、リポジトリからの削除は必須。



---



\### Phase B: 中優先度（研究の質向上）— 推定 30h



\#### B-1: Citation Stance 分類（4h）



\*\*目的\*\*: 引用が「支持」「反論」「中立」かを分類。



\*\*現状\*\*: `jarvis\_core/citation/` にモジュールが存在するが CLI 未接続。



\*\*実装方針\*\*:

1\. `jarvis\_core/citation/` の既存コードを確認し、`classify\_stance(paper\_a, paper\_b)` 的な関数を特定。

2\. `jarvis\_cli/citation\_stance.py` を新設、CLI コマンド `citation-stance` を登録。

3\. 入力 JSON の全ペアについて stance を判定し、結果を JSON で出力。



\#### B-2: Contradiction 検出の改善（6h）



\*\*目的\*\*: 現在のルールベース検出は 3 論文ペアで 0 件。LLM を使った意味的矛盾検出に切り替え。



\*\*現状\*\*: `jarvis\_cli/contradict.py` が `jarvis\_core/contradiction/` を呼んでいるが、ルールベースのため検出精度が低い。



\*\*実装方針\*\*:

1\. `jarvis\_core/contradiction/` の既存コードに Gemini API ベースの分類器を追加。

2\. 各ペアの abstract を Gemini に投げ、「矛盾あり/なし/不明」を判定。

3\. `contradict.py` に `--use-llm` フラグを追加。



\#### B-3: Paper Scoring（5h）



\*\*目的\*\*: 被引用数・エビデンスレベル・出版年・ジャーナル影響度を組み合わせた独自スコア。



\*\*現状\*\*: `jarvis\_core/paper\_scoring/` にディレクトリが存在するが中身は雛形のみ。



\*\*実装方針\*\*:

1\. スコア計算式を定義（例: `score = 0.3\*norm\_citations + 0.3\*evidence\_score + 0.2\*recency + 0.2\*journal\_tier`）。

2\. `jarvis\_cli/score.py` を新設、CLI コマンド `score` を登録。

3\. pipeline の Step 3 後に自動スコアリングを追加。



\#### B-4: Active Learning Screening（8h）



\*\*目的\*\*: 人間がラベル付けした論文（relevant/irrelevant）を学習し、残りを自動スクリーニング。



\*\*現状\*\*: `jarvis\_core/active\_learning/` に雛形あり。



\*\*実装方針\*\*:

1\. 既存の雛形を確認し、`ActiveLearner` クラスの実装状態を把握。

2\. 簡易版: TF-IDF + ロジスティック回帰で実装。

3\. CLI コマンド `screen` を新設（`jarvis screen --db papers.json --labels labels.csv`）。



\#### B-5: Obsidian ノートテンプレート強化（3h）



\*\*目的\*\*: PICO 抽出結果、エビデンスバッジ、関連論文リンクをフロントマターに追加。



\*\*現状\*\*: `obsidian\_export.py` は title, authors, year, journal, DOI, evidence\_level をフロントマターに出力。



\*\*実装方針\*\*:

1\. `jarvis\_core/evidence/schema.py` の `PICOExtraction` データクラスを活用。

2\. evidence grading 時に PICO を抽出し、Obsidian ノートのフロントマターに `population`, `intervention`, `comparator`, `outcome` を追加。

3\. 同一 pipeline 実行内の論文同士を `\[\[リンク]]` で相互参照。



\#### B-6: Streamlit Dashboard 拡張（6h）



\*\*目的\*\*: `app.py` のダッシュボードに evidence, pipeline, contradict の結果表示を追加。



\*\*現状\*\*: `app.py` は検索結果の表示のみ。



\*\*実装方針\*\*:

1\. `logs/pipeline/` の JSON を読み込み、evidence 分布グラフ（棒グラフ）を表示。

2\. 矛盾ペアのネットワーク図を表示。

3\. 実行ログの一覧テーブルを追加。



---



\### Phase C: 低優先度（エコシステム拡張）— 推定 50h+



| # | タスク | 推定時間 | 備考 |

|---|---|---|---|

| C-1 | MCP Hub（PubMed/S2/OpenAlex を MCP プロトコルで統合） | 15h | README にのみ記載。MCP 仕様の理解が必要 |

| C-2 | Browser Agent（Web ページからの論文抽出） | 12h | `jarvis\_core/browser/` に雛形あり。セキュリティポリシー必要 |

| C-3 | Skills System（プラグイン拡張機構） | 10h | README にのみ記載 |

| C-4 | Multi-Agent Orchestrator（複数 AI 協調） | 15h | README にのみ記載 |

| C-5 | arXiv/Crossref の UnifiedSourceClient 統合 | 3h | クライアントは `jarvis\_core/sources/` に存在。SourceType enum に追加するだけ |

| C-6 | Zotero コレクション指定 | 2h | config.yaml の `zotero.collection` を使い `zot.create\_items()` にコレクションキーを渡す |



---



\## 11. 実装時の注意事項



\### 11.1 ファイル書き込み方法



PowerShell から Python コードを直接 `python -c "..."` で書き込む方法は、特殊文字（`e.g.`, `{}`, `:` 等）が PowerShell に解釈されてエラーになる。必ず以下の方法を使うこと：



```

方法1: notepad <filename> で手動貼り付け

方法2: write\_<task>.py スクリプトを作成し python write\_<task>.py で実行

方法3: fix\_<target>.py で対象ファイル全体を上書き

```



\### 11.2 `\_\_init\_\_.py` の編集



`jarvis\_cli/\_\_init\_\_.py` への部分挿入は過去に複数回失敗している。新コマンドを追加する際は \*\*ファイル全体を上書き\*\* すること。現在のファイルは約 200 行で、`dispatch` 辞書にコマンド名と関数のマッピングがある。



\### 11.3 テストデータ



`logs/search/test\_evidence.json` および `logs/search/test\_evidence\_evidence.json` がテスト用に存在する（3 論文: RCT, systematic review, case report）。ただし `logs/` は .gitignore で除外されているため、新しい環境では再作成が必要。



\### 11.4 Gemini API の利用制限



無料枠: 1,500 requests/日、15 RPM。50 論文の要約生成は約 50 リクエストなので余裕がある。ただし短時間に連続実行すると RPM 上限に達する。



---



\## 12. 関連リポジトリ



| リポジトリ | 用途 | 備考 |

|---|---|---|

| https://github.com/kaneko-ai/jarvis-ml-pipeline | メインリポジトリ | 本文書の対象 |

| https://github.com/kaneko-ai/zotero-doi-importer | Zotero DOI 登録ツール（FastAPI） | \*\*⚠️ .env に旧 API キーが公開中\*\*。削除必要 |



---



\## 13. 用語集



| 用語 | 説明 |

|---|---|

| CEBM Oxford Scale | Centre for Evidence-Based Medicine のエビデンスレベル分類（1a〜5） |

| RRF | Reciprocal Rank Fusion。複数の検索ランキングを統合する手法 |

| PRISMA 2020 | 系統的レビューの報告ガイドライン。フローチャートで文献選択過程を図示 |

| PICO | Population, Intervention, Comparator, Outcome の頭文字。臨床研究の構造化フレームワーク |

| UnifiedSourceClient | PubMed/S2/OpenAlex を統一インターフェースで検索するクライアント |

| EnsembleClassifier | ルールベース + LLM の重み付け平均でエビデンスレベルを判定する分類器 |

