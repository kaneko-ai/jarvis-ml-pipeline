HANDOVER\_v4.md — JARVIS Research OS 引き継ぎ書 v4

作成日: 2026-03-02

前版: HANDOVER\_v3.md（2026-03-02、コミット b27d72b8 時点）

対象リポジトリ: https://github.com/kaneko-ai/jarvis-ml-pipeline

ブランチ: main

最新プッシュ済みコミット: 5c043b02 — "Phase A: LLM summary (A-1), S2 retry (A-2), fuzzy dedup (A-3), PRISMA (A-4), BibTeX (A-5)"（2026-03-01T18:56:58Z）

関連リポジトリ: https://github.com/kaneko-ai/zotero-doi-importer（A-6 完了済み、コミット 0cb2447）

本書の目的: この文書を読んだ AI または開発者が、追加の質問なしに環境理解→残タスク実装まで100%再現・継続できることを保証する。



1\. プロジェクト概要

JARVIS Research OS は、系統的文献レビュー（Systematic Literature Review）を自動化するローカルファースト AI アシスタント。CLI コマンド 1 つで「論文検索 → 重複除去 → エビデンス判定 → スコアリング → LLM日本語要約 → Obsidian ノート作成 → Zotero 登録 → PRISMA図生成 → BibTeX出力」を一括実行できる。



主な利用者: 大学院生（プログラミング初学者、Windows環境）

主な用途: PD-1免疫療法、スペルミジン、免疫老化・オートファジーなどの研究テーマに関する文献調査



2\. 開発環境（実機ステータス 2026-03-02 時点）

項目	値

OS	Windows 11

シェル	PowerShell 5.1

Python	3.12.3

Node.js	v24.13.1

プロジェクトパス	C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline

venv パス	.venv （プロジェクトルート直下）

venv 有効化	.\\.venv\\Scripts\\Activate.ps1

Python 実体	C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline\\.venv\\Scripts\\python.exe

Obsidian Vault	C:\\Users\\kaneko yu\\Documents\\ObsidianVault

2.1 環境変数（.env）

.env はプロジェクトルートに存在し、Git 追跡外（.gitignore で除外済み）。



GEMINI\_API\_KEY=<39文字のGemini APIキー>

LLM\_PROVIDER=gemini

ZOTERO\_API\_KEY=<2026-03-02に新規発行済み>

ZOTERO\_USER\_ID=16956010

2.2 インストール済み主要パッケージ（.venv内）

jarvis-research-os==1.0.0（pip install -e . でインストール）

google-genai==1.65.0

python-dotenv==1.2.2

rank-bm25==0.2.2

sentence-transformers（all-MiniLM-L6-v2 モデル自動DL済み）

pyzotero

requests==2.32.5

streamlit==1.54.0

rapidfuzz==3.14.3

scikit-learn（Active Learning用）

pyyaml

2.3 venv内のpipに関する重要な注意

セッション中に発見・修正した問題: venv に pip が存在しなかったため、pip install がシステム Python（C:\\Users\\kaneko yu\\AppData\\Local\\Programs\\Python\\Python312\\）にインストールされていた。python -m ensurepip --upgrade で修復済み。



今後のルール: パッケージインストールには必ず python -m pip install <package> を使用すること（素の pip install はシステム側を使うリスクがある）。



2.4 未インストール・接続不可のコンポーネント

コンポーネント	状態	備考

Ollama（ローカルLLM）	未起動・未インストール	use\_llm=False で回避中

pandas 3.0.0	インストール失敗	現在の機能では不要

3\. タスク完了状況の全体マップ

v2 タスク（全8件 — 全完了・マージ済み）

タスク	内容	状態

T1-2	UnifiedSourceClient を CLI に接続	✅ 完了

T1-3	セキュリティ整備（.gitignore, backup.ps1）	✅ 完了

T2-1	EnsembleClassifier を CLI に接続	✅ 完了

T2-2	Obsidian Vault 直接出力	✅ 完了

T3-1	semantic-search コマンド	✅ 完了

T3-2	contradict コマンド	✅ 完了

T3-3	Zotero 連携（zotero-sync）	✅ 完了

T4-1	pipeline コマンド（全工程一括実行）	✅ 完了

Phase A: 高優先度（全6件 — 全完了）

タスク	内容	状態	コミット	備考

A-6	zotero-doi-importer の .env 削除	✅ 完了	0cb2447（zotero-doi-importer repo）	git rm --cached .env で追跡除外。APIキーはローテーション済み

A-1	LLM要約の pipeline 統合	✅ 完了	5c043b02（jarvis-ml-pipeline）	\_step\_summarize() 追加。Gemini API で日本語要約生成。--no-summary フラグ対応

A-2	Semantic Scholar 429 リトライ	✅ 完了	5c043b02	semantic\_scholar\_client.py に指数バックオフ（5s→10s→30s、最大3回）追加。実際に429発生→自動回復を確認済み

A-3	重複除去の精度向上（fuzzy match）	✅ 完了	5c043b02	rapidfuzz.fuzz.ratio >= 90 による3段階判定（DOI→タイトル完全一致→fuzzy）

A-4	PRISMA ダイアグラムの pipeline 統合	✅ 完了	5c043b02	--prisma フラグ。Mermaid .mmd + Markdown .md を logs/pipeline/ に出力

A-5	BibTeX の pipeline 統合	✅ 完了	5c043b02	--bibtex フラグ。.bib ファイルを logs/pipeline/ に出力

Phase B: 中優先度（6件中 5件完了、1件未着手）

タスク	内容	状態	備考

B-5	Obsidian ノートテンプレート強化	✅ 完了	Evidence Level バッジ、study\_type、keywords、Related Papers セクション追加。obsidian\_export.py 上書き済み

B-3	Paper Scoring CLI + pipeline 統合	✅ 完了	jarvis\_cli/score.py 新設。pipeline に Step 4/7 として組み込み。Grade A-F で評価。基礎研究は Level 5 + 被引用0 のため Grade F（正常動作）

B-1	Citation Stance 分類	✅ 完了	jarvis\_core/citation/stance\_classifier.py 新設。CitationStance enum に SUPPORT, CONTRAST, CONTRADICT（後方互換）, NEUTRAL, MENTION を定義。graph.py との互換性修正済み。CLI citation-stance コマンド追加。--no-llm でキーワードヒューリスティック、なしでGemini API使用

B-2	Contradiction 検出の改善（LLM対応）	✅ 完了	jarvis\_core/contradiction/detector.py 上書き。schema.ContradictionResult に統一。--use-llm フラグでGemini API意味的矛盾検出。ヒューリスティックモードで6ペア・0矛盾（同テーマのため正常）

B-4	Active Learning Screening	✅ 完了	jarvis\_cli/screen.py 新設。jarvis screen コマンド。--auto モードでキーワードベース自動ラベリング、インタラクティブモード対応。scikit-learn依存。テスト結果：4論文中1件relevant、work saved 25%

B-6	Streamlit Dashboard 拡張	❌ 未着手	app.py に evidence分布グラフ、矛盾ネットワーク図、実行ログ一覧を追加する予定

Phase C: 低優先度（全件未着手）

タスク	内容	推定時間	備考

C-1	MCP Hub統合	15h	MCP プロトコルでPubMed/S2/OpenAlexを統合

C-2	Browser Agent	12h	jarvis\_core/browser/ に雛形あり

C-3	Skills System	10h	READMEにのみ記載

C-4	Multi-Agent Orchestrator	15h	READMEにのみ記載

C-5	arXiv/Crossref の UnifiedSourceClient 統合	3h	クライアントは jarvis\_core/sources/ に存在。SourceType enum に追加するだけ

C-6	Zotero コレクション指定	2h	config.yaml の zotero.collection 活用

4\. 未プッシュのローカル変更（重要）

Phase A コミット 5c043b02 がリモートの最新。Phase B の変更（B-5, B-3, B-1, B-2, B-4）はローカルで動作確認済みだが、まだ git commit/push されていない。 次のセッションで最初にやるべきことは：



Copycd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1

git status

git add jarvis\_cli/\_\_init\_\_.py jarvis\_cli/pipeline.py jarvis\_cli/obsidian\_export.py jarvis\_cli/score.py jarvis\_cli/citation\_stance.py jarvis\_cli/contradict.py jarvis\_cli/screen.py jarvis\_core/citation/stance\_classifier.py jarvis\_core/contradiction/detector.py

git diff --cached --stat

git commit -m "Phase B: Obsidian template (B-5), Paper Scoring (B-3), Citation Stance (B-1), Contradiction LLM (B-2), Active Learning (B-4)"

git push origin main

注意: jarvis\_core/sources/semantic\_scholar.py（0バイトの空ファイル）が存在する場合は削除すること：



CopyRemove-Item jarvis\_core\\sources\\semantic\_scholar.py -ErrorAction SilentlyContinue

実体は semantic\_scholar\_client.py（8150バイト → A-2 でリトライ追加版に上書き済み）。



5\. 現在の CLI コマンド一覧（16コマンド）

コマンド	使用例	状態

search	jarvis search "PD-1" --max 5 --sources pubmed,s2,openalex	✅

merge	jarvis merge file1.json file2.json -o merged.json	✅

note	jarvis note input.json --provider gemini --obsidian	✅

citation	jarvis citation input.json	✅

prisma	jarvis prisma file1.json file2.json -o prisma.md	✅

bibtex	search/merge の --bibtex フラグ経由	✅

evidence	jarvis evidence input.json	✅

obsidian-export	jarvis obsidian-export input.json	✅

semantic-search	jarvis semantic-search "query" --db file.json --top 10	✅

contradict	jarvis contradict input.json \[--use-llm]	✅ (B-2更新済み)

zotero-sync	jarvis zotero-sync input.json	✅

pipeline	jarvis pipeline "query" --max 50 --obsidian --zotero --prisma --bibtex --no-summary	✅ (A-1〜A-5更新済み)

score	jarvis score input.json	✅ (B-3新設)

citation-stance	jarvis citation-stance input.json \[--no-llm]	✅ (B-1新設)

screen	jarvis screen input.json \[--auto] \[--batch-size 5] \[--budget 50]	✅ (B-4新設)

run	jarvis run --config pipeline.yaml	v1から存在

5.1 pipeline コマンドの現在の実行フロー（7ステップ）

jarvis pipeline "immunosenescence autophagy" --max 10 --obsidian --zotero --prisma --bibtex



&nbsp; ├─ Step 1/7: \_step\_search()      → UnifiedSourceClient (PubMed+OpenAlex)

&nbsp; │                                   フォールバック: PubMedClient のみ

&nbsp; ├─ Step 2/7: \_step\_dedup()       → DOI完全一致 → タイトル完全一致 → fuzzy match (>=90%)

&nbsp; ├─ Step 3/7: \_step\_evidence()    → grade\_evidence(use\_llm=False) + \_fallback\_classify()

&nbsp; ├─ Step 4/7: \_step\_score()       → PaperScorer (citation×0.3 + evidence×0.3 + recency×0.2 + journal×0.2)

&nbsp; ├─ Step 5/7: \_step\_summarize()   → LLMClient(Gemini) で日本語要約生成 (--no-summary で省略可)

&nbsp; ├─ Step 6/7: エクスポート

&nbsp; │   ├─ JSON保存                  → logs/pipeline/<query>\_<timestamp>.json

&nbsp; │   ├─ Obsidian出力 (--obsidian) → config.yaml の vault\_path/JARVIS/Papers/

&nbsp; │   ├─ Zotero同期 (--zotero)     → Crossref metadata → pyzotero create\_items

&nbsp; │   ├─ PRISMA図 (--prisma)       → logs/pipeline/<run>\_prisma.md + .mmd

&nbsp; │   └─ BibTeX (--bibtex)         → logs/pipeline/<run>.bib

&nbsp; └─ Step 7/7: 実行ログ保存        → logs/pipeline/<query>\_<timestamp>\_log.json

6\. 変更されたファイル一覧（v3→v4 の差分）

ファイルパス	変更内容	バイト数

jarvis\_cli/\_\_init\_\_.py	pipeline の --no-summary/--prisma/--bibtex 追加、score/citation-stance/contradict --use-llm/screen サブコマンド追加	9217

jarvis\_cli/pipeline.py	7ステップ化（score/summarize追加）、fuzzy dedup、PRISMA/BibTeX統合	16876

jarvis\_cli/obsidian\_export.py	Evidence Level バッジ、study\_type、keywords、Related Papers セクション	7477

jarvis\_cli/score.py	新規作成 PaperScorer CLI ラッパー	4608

jarvis\_cli/citation\_stance.py	新規作成 Citation Stance CLI	3159

jarvis\_cli/contradict.py	B-2で上書き。schema.ContradictionResult統一、--use-llm対応	4245

jarvis\_cli/screen.py	新規作成 Active Learning Screening CLI	7718

jarvis\_core/citation/stance\_classifier.py	新規作成 CitationStance enum (SUPPORT/CONTRAST/CONTRADICT/NEUTRAL/MENTION)、StanceClassifier、LLM+キーワード二重方式	7481

jarvis\_core/contradiction/detector.py	B-2で上書き。LLM対応、schema.ContradictionResult統一	7371

jarvis\_core/sources/semantic\_scholar\_client.py	A-2: 指数バックオフリトライ追加（5s→10s→30s）	Phase Aコミット含む

7\. 既知の問題と回避策

\#	問題	原因	回避策

1	Evidence grading で Ollama エラー	未起動	use\_llm=False で回避（pipeline.py 対応済み）

2	基礎研究論文が全て Level 5	ルールベース分類器の限界	\_fallback\_classify() でキーワード拡張済み。Level 5は正常（基礎研究に該当）

3	S2 429 Too Many Requests	無料枠 100req/5min	A-2で指数バックオフ実装済み。それでも超過時はPubMed+OpenAlexがフォールバック

4	PowerShell で python -c "..." がエラー	{} : 等がPowerShell解釈される	別途 .py ファイルを作成して python filename.py で実行

5	\_\_init\_\_.py への部分挿入が不安定	文字列操作の問題	全文上書き方式のみ使用すること（write\_\*.py スクリプトで対応）

6	Paper Scoring で全論文 Grade F	基礎研究 Level 5 + 被引用数0	正常動作。臨床試験論文（RCT等）なら高グレードになる

7	LLM要約が一部論文で生成されない	abstract が空の論文	正常動作（abstract がない論文はスキップ）

8	pip が venv 外にインストールする	venv に pip が未設定だった	python -m ensurepip --upgrade で修復済み。今後は python -m pip install を使用

8\. 重要な import パス一覧

Copy# Sources

from jarvis\_core.sources import UnifiedSourceClient

from jarvis\_core.sources.unified\_source\_client import SourceType

from jarvis\_core.sources import PubMedClient, SemanticScholarClient, OpenAlexClient



\# Evidence

from jarvis\_core.evidence import grade\_evidence

\# grade\_evidence(title="...", abstract="...", use\_llm=False) → EvidenceGrade



\# Embeddings / Hybrid Search

from jarvis\_core.embeddings import HybridSearch



\# Obsidian export

from jarvis\_cli.obsidian\_export import export\_papers\_to\_obsidian



\# Zotero

from jarvis\_cli.zotero\_sync import \_get\_zotero\_client, \_build\_zotero\_item, \_get\_crossref\_metadata



\# LLM

from jarvis\_core.llm.llm\_utils import LLMClient, Message



\# Paper Scoring

from jarvis\_core.paper\_scoring.scorer import PaperScorer, calculate\_paper\_score



\# Citation Stance

from jarvis\_core.citation.stance\_classifier import CitationStance, StanceClassifier, classify\_citation\_stance



\# Contradiction

from jarvis\_core.contradiction.detector import ContradictionDetector

from jarvis\_core.contradiction.schema import Claim, ContradictionResult



\# Active Learning

from jarvis\_core.active\_learning import ActiveLearningEngine

Copy

9\. config.yaml 構造

Copyobsidian:

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

&nbsp; use\_llm: false

&nbsp; strategy: weighted\_average

10\. スモークテスト手順（新セッション開始時）

Copy# 1. 移動と仮想環境有効化

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1



\# 2. Python が venv 内か確認

python -c "import sys; print(sys.executable)"

\# → .venv\\Scripts\\python.exe が表示されること



\# 3. CLI ヘルプ確認

python -m jarvis\_cli --help



\# 4. 簡易 pipeline テスト（要約なし＝API不使用で高速）

python -m jarvis\_cli pipeline "autophagy" --max 3 --no-summary



\# 5. フル pipeline テスト

python -m jarvis\_cli pipeline "PD-1 immunotherapy" --max 3 --obsidian --prisma --bibtex



\# 6. import 確認

python -c "from jarvis\_core.sources import UnifiedSourceClient; print('OK')"

python -c "from jarvis\_core.evidence import grade\_evidence; print('OK')"

python -c "from jarvis\_core.citation.stance\_classifier import CitationStance; print('OK')"

python -c "from jarvis\_core.contradiction.detector import ContradictionDetector; print('OK')"

python -c "from jarvis\_core.paper\_scoring.scorer import PaperScorer; print('OK')"

11\. 残タスク一覧と実装ガイド

11.1 最優先: Phase B のコミット \& プッシュ

Phase B の変更はローカルのみ。セッション開始直後に以下を実行：



Copygit status

git add jarvis\_cli/\_\_init\_\_.py jarvis\_cli/pipeline.py jarvis\_cli/obsidian\_export.py jarvis\_cli/score.py jarvis\_cli/citation\_stance.py jarvis\_cli/contradict.py jarvis\_cli/screen.py jarvis\_core/citation/stance\_classifier.py jarvis\_core/contradiction/detector.py

git commit -m "Phase B: Obsidian template (B-5), Paper Scoring (B-3), Citation Stance (B-1), Contradiction LLM (B-2), Active Learning (B-4)"

git push origin main

11.2 B-6: Streamlit Dashboard 拡張（推定6h）

目的: app.py に evidence 分布グラフ、矛盾ネットワーク図、実行ログ一覧を追加。



現状: app.py（11692バイト）は検索結果の表示のみ。streamlit==1.54.0 インストール済み。



実装方針:



logs/pipeline/ の \*\_log.json を一覧表示するページを追加。

各実行ログから evidence 分布を棒グラフ（st.bar\_chart または plotly）で表示。

\*\_stance.json / \*\_contradictions.json があればネットワーク図を描画。

pipeline JSON を読み込み、論文テーブルを表示（score、evidence\_level、summary\_ja 含む）。

検証: streamlit run app.py → ブラウザで確認。



11.3 Phase C（低優先度、全6件未着手）

\#	タスク	推定時間	備考

C-1	MCP Hub	15h	MCP プロトコル理解が前提

C-2	Browser Agent	12h	jarvis\_core/browser/ に雛形あり

C-3	Skills System	10h	プラグイン拡張機構

C-4	Multi-Agent Orchestrator	15h	複数AI協調

C-5	arXiv/Crossref の UnifiedSourceClient 統合	3h	SourceType enum に追加＋クライアント接続

C-6	Zotero コレクション指定	2h	config.yaml の zotero.collection 活用

推奨順序: C-5 → C-6（簡単、即効果）→ B-6（可視化）→ C-2 → C-1 → C-3 → C-4



12\. 実装時の絶対ルール

PowerShell から python -c "..." で複雑なコードを実行しない。必ず .py ファイルを作成して python filename.py で実行する。

jarvis\_cli/\_\_init\_\_.py は全文上書きのみ。部分挿入は過去に複数回失敗している。write\_\*.py スクリプトで全ファイルを書き出す方式を厳守。

パッケージインストールは python -m pip install。素の pip install はシステム Python 側にインストールされるリスクがある。

logs/ ディレクトリは .gitignore で除外されている。テストデータは新環境では再作成が必要（pipeline を1回実行すれば生成される）。

Gemini API 無料枠: 1,500 req/日、15 RPM。50論文の要約は余裕だが、連続テストで RPM 上限に注意。

Semantic Scholar 無料枠: 100 req/5min。A-2 のリトライ（5s→10s→30s）で自動回復するが、大量検索は PubMed+OpenAlex 推奨。

13\. Git コミット履歴（時系列）

5c043b02  Phase A: LLM summary (A-1), S2 retry (A-2), fuzzy dedup (A-3), PRISMA (A-4), BibTeX (A-5)  ← リモート最新

5feb8515  HANDOVER\_v3.md v2 + v318

b27d72b8  Fix: \_\_init\_\_.py の未コミット変更を反映

cd2b0206  Improve: evidence grading にキーワードフォールバックを追加

429e6362  Fix: zotero-sync を create\_items 方式に変更 + コマンド登録修正

f16fc286  T3-3: Zotero 連携 (zotero-sync コマンド, pyzotero使用)

f75ef42d  Fix: semantic-search の HybridSearchResult len() エラーを修正

48873197  T3-1 + T3-2: semantic-search と contradict コマンドを新設

538d5a83  T2-2: Obsidian Vault 直接出力

88c87a95  T2-1: EnsembleClassifier を CLI に接続

dcd172a2  venv/ を Git 追跡から除外

38af0576  T1-3: セキュリティ整備

516eeac7  T1-2: UnifiedSourceClient を CLI に接続



\[ローカル未プッシュ — Phase B: B-5, B-3, B-1, B-2, B-4]

14\. 関連リポジトリ

リポジトリ	用途	状態

https://github.com/kaneko-ai/jarvis-ml-pipeline	メインリポジトリ	Phase A プッシュ済み、Phase B ローカルのみ

https://github.com/kaneko-ai/zotero-doi-importer	Zotero DOI 登録ツール	A-6完了（.env 追跡除外、コミット 0cb2447）

15\. 用語集

用語	説明

CEBM Oxford Scale	Centre for Evidence-Based Medicine のエビデンスレベル分類（1a〜5）

RRF	Reciprocal Rank Fusion — 複数検索ランキングの統合手法

PRISMA 2020	系統的レビューの報告ガイドライン。文献選択過程をフローチャートで図示

PICO	Population, Intervention, Comparator, Outcome — 臨床研究の構造化フレームワーク

UnifiedSourceClient	PubMed/S2/OpenAlex を統一インターフェースで検索するクライアント

EnsembleClassifier	ルールベース + LLM の重み付け平均でエビデンスレベルを判定する分類器

rapidfuzz	文字列類似度計算ライブラリ。fuzzy dedup に使用

ActiveLearningEngine	不確実性サンプリングによる効率的文献スクリーニングエンジン

