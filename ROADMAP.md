# JARVIS Research OS — Master Roadmap
# 作成日: 2026-02-27
# 最終更新: 2026-02-27
# 対象者: kaneko（利用者本人）/ AI開発アシスタント（ChatGPT, Gemini, Claude）

---

## 0. このドキュメントの目的

このmdは「道を逸れない」ための絶対的な設計書である。
AI に開発を依頼する際は、必ずこのファイル全文を最初に渡すこと。
AI はここに書かれていない機能追加・技術変更を提案してはならない。

---

## 1. プロジェクト概要

| 項目 | 値 |
|---|---|
| プロジェクト名 | JARVIS Research OS |
| リポジトリ | https://github.com/kaneko-ai/jarvis-ml-pipeline |
| バージョン | 4.2.0 (pip) / 1.0.0 (jarvis_core) |
| 利用者 | kaneko 1名のみ（個人利用） |
| 目的 | 大学院（京大・がん免疫応答制御部門）での PD-1 / スペルミジン研究を AI で支援する |
| 最終ビジョン | OpenClaw のような、研究から私生活まで全面支援する常駐型パーソナル AI |
| 現フェーズ | CLI を「毎日使える」レベルに整備する（UIは後） |

---

## 2. 絶対に守るルール（AI向け）

### 2.1 やってよいこと
- jarvis-ml-pipeline の Python コードの修正・追加
- 既存 CLI コマンドのバグ修正
- 新しい CLI コマンドの追加（このロードマップに記載されたもののみ）
- テストの追加・修正
- ドキュメントの追加・修正

### 2.2 やってはならないこと
- jarvis-desktop（Tauri/Rust/React）への作業（凍結中）
- Tauri, Electron, その他デスクトップフレームワークの導入提案
- このロードマップに記載のないフェーズの先取り実装
- 既存の動作する機能の大規模リファクタリング（まず動かすことが最優先）
- OpenAI API キーの購入や有料サービスの前提とする設計
- ローカル LLM（Ollama）の導入（GPU なし環境のため当面見送り）

### 2.3 技術制約
- OS: Windows 11 Home
- CPU: i7-1065G7 (4コア, 1.30GHz)
- RAM: 16GB
- GPU: なし（Intel Iris Plus 統合グラフィックス）
- ディスク空き: 35.6GB
- Python: 3.12.3 (venv 使用)
- LLM バックエンド（優先順）:
  1. Gemini API (Free Tier, GEMINI_API_KEY 設定済み)
  2. Codex CLI (ChatGPT Plus, codex-cli 0.104.0, 認証済み)
- PowerShell 5.1 環境（UTF-8 BOM 必須）

---

## 3. アーキテクチャ方針

### 3.1 LLM バックエンド戦略（二段構え）

| 用途 | バックエンド | 理由 |
|---|---|---|
| 日常の API 呼び出し（検索、要約、分類） | Gemini API (gemini-2.0-flash) | 無料枠で十分、高速 |
| 深い推論（複雑な論文分析、矛盾検出） | Codex CLI → GPT-5 系 | 高精度、ただし5h制限あり |

実装方針: LLMClient に `codex` プロバイダを追加。
codex-python-sdk (https://github.com/spdcoding/codex-python-sdk) を利用するか、
subprocess で `codex exec --output-last-message` を呼ぶラッパーを作成。

### 3.2 データフロー

Copy
[ユーザー] → CLI コマンド ↓ [論文検索] PubMed API / arXiv API / Crossref API / Semantic Scholar API ↓ [ローカル保存] JSONL ファイル（papers.jsonl） ↓ [分析] Gemini API で要約・エビデンスグレーディング・スコアリング ↓ (必要な場合のみ) [深い分析] Codex CLI で矛盾検出・詳細レビュー ↓ [出力] Markdown / BibTeX / RIS / Zotero連携 ↓ [UI（将来）] Streamlit ダッシュボード


### 3.3 データはすべてローカル保存
- 論文メタデータ: `data/papers.jsonl`
- 分析結果: `logs/runs/{run_id}/`
- 検索インデックス: `data/index/`
- 設定: `config.yaml`
- API にはクエリとアブストラクトのみ送信。PDF 本文は送信しない。

---

## 4. フェーズ定義

### Phase 0: 基盤修復（Week 1: 2/27〜3/5）
**ゴール: `jarvis run` が正常に動作する**

- [ ] P0-1: google-generativeai パッケージのインストール
  - `pip install google-generativeai`
  - 確認: `python -c "from google import genai; print('OK')"`

- [ ] P0-2: `jarvis run` の動作確認
  - `python -m jarvis_cli run --goal "PD-1" --category paper_survey`
  - エラーが出たら一つずつ修正

- [ ] P0-3: 不足している依存パッケージの一括インストール
  - `pip install -e ".[all]"` を試す
  - sentence-transformers はサイズが大きいため、必要になるまで保留

- [ ] P0-4: PubMed 検索が実際に論文を返すことの確認
  - jarvis_core/sources/ のPubMed/arXiv/Crossrefクライアントの動作テスト
  - `python -c "from jarvis_core.sources.pubmed import PubMedClient; c=PubMedClient(); print(c.search('PD-1', max_results=3))"`
  - 動かない場合はソースコードを確認して修正

- [ ] P0-5: 基本的な検索→保存フローの確立
  - 検索結果が `data/` 以下に JSONL として保存されることを確認

**完了条件: ターミナルで PD-1 を検索して論文リストが表示される**

### Phase 1: コア機能の実用化（Week 2: 3/6〜3/12）
**ゴール: 検索→分析→保存の一貫パイプラインが動く**

- [ ] P1-1: Evidence Grading の動作確認
  - `from jarvis_core.evidence import grade_evidence` が動くか確認
  - 論文のタイトルとアブストラクトからエビデンスレベル（1a-5）を付与

- [ ] P1-2: Paper Scoring の動作確認
  - 品質スコアの算出が動くか確認

- [ ] P1-3: 要約機能の実装/修復
  - Gemini API を使って各論文のアブストラクトを日本語で要約
  - 要約結果を JSONL に追記保存

- [ ] P1-4: `jarvis search` コマンドの実装（もし存在しなければ）
  - 自然言語のクエリ → PubMed + arXiv + Crossref 横断検索
  - 結果を JSONL に保存
  - 各論文にエビデンスレベルと品質スコアを付与
  - 上位10件のアブストラクトを日本語で要約

- [ ] P1-5: Markdown エクスポート
  - 検索結果をまとめた見やすい Markdown ファイルを生成
  - 形式: タイトル / 著者 / 年 / DOI / エビデンスレベル / スコア / 要約

- [ ] P1-6: BibTeX / RIS エクスポートの動作確認
  - `python -m jarvis_cli export --format bibtex --input data/papers.jsonl --output refs.bib`

**完了条件: PD-1 で検索 → エビデンスレベル付き論文リスト → Markdown + BibTeX 出力**

### Phase 2: Codex CLI 統合 + 高度分析（Week 3: 3/13〜3/19）
**ゴール: GPT-5 系による深い論文分析ができる**

- [ ] P2-1: LLMClient に codex プロバイダを追加
  - `codex exec` を subprocess で呼ぶラッパーを実装
  - または codex-python-sdk を利用
  - `LLM_PROVIDER=codex` で切り替え可能にする

- [ ] P2-2: 引用分析（Citation Analysis）の動作確認
  - 論文間の支持/反論/言及の分類

- [ ] P2-3: PRISMA 図生成の動作確認
  - `python -m jarvis_cli export --format prisma`

- [ ] P2-4: papers コマンドの動作確認
  - `python -m jarvis_cli papers tree` — 引用ツリー
  - `python -m jarvis_cli papers map3d` — 3D 論文マップ

- [ ] P2-5: harvest / radar の動作確認
  - `python -m jarvis_cli harvest watch` — 新着論文の監視
  - `python -m jarvis_cli radar run` — R&D レーダー

**完了条件: Codex CLI 経由で論文の深い分析ができ、引用関係の可視化が動く**

### Phase 3: 研究知識ベースの構築（Week 4: 3/20〜3/31）
**ゴール: 研究室配属までに PD-1/スペルミジンの知識ベースを完成**

- [ ] P3-1: PD-1 関連の主要論文を網羅的に収集
  - キーワード: "PD-1", "PD-L1", "immune checkpoint", "Honjo"
  - 目標: 100件以上

- [ ] P3-2: スペルミジン関連論文の収集
  - キーワード: "spermidine", "autophagy", "immune", "T cell"
  - 目標: 50件以上

- [ ] P3-3: 本庶佑先生の主要論文リスト作成
  - Semantic Scholar / PubMed で著者検索

- [ ] P3-4: 勉強ノートの自動生成
  - 収集した論文を元に以下のノートを Gemini API で生成:
    - 「PD-1 とは何か：発見から臨床応用まで」
    - 「スペルミジンの免疫における役割」
    - 「がん免疫応答制御の現在のフロンティア」

- [ ] P3-5: Zotero への取り込み
  - BibTeX / RIS エクスポート → Zotero インポート

- [ ] P3-6: Screen コマンドで論文の重要度スクリーニング
  - Active Learning を使って効率的に重要論文を選別

**完了条件: PD-1/スペルミジンの主要論文リスト + 勉強ノート + Zotero ライブラリが完成**

### Phase 4: Streamlit ダッシュボード（4月以降）
**ゴール: ボタン操作で全機能が連動する UI**

- [ ] P4-1: Streamlit の基本セットアップ
  - `pip install streamlit plotly`
  - 基本画面: 検索ボックス + 結果テーブル + 分析パネル

- [ ] P4-2: 検索 → 分析 → 保存の一連の操作を UI 化
- [ ] P4-3: 論文間の関連性を視覚的に表示（plotly グラフ）
- [ ] P4-4: 引用ネットワークの可視化
- [ ] P4-5: PRISMA 図の表示
- [ ] P4-6: エビデンスレベルによるフィルタリング/ソート

**完了条件: ブラウザで localhost:8501 を開いてボタン操作で全機能が使える**

### Phase 5: OpenClaw 化（将来）
**ゴール: 研究から私生活まで全面支援する常駐型パーソナル AI**

- [ ] P5-1: Discord / Telegram / LINE 連携
- [ ] P5-2: スケジュール実行（定時論文チェック、リマインダー）
- [ ] P5-3: メモリ/コンテキストの永続化
- [ ] P5-4: スキルシステムの整備（OpenClaw の skills 概念）
- [ ] P5-5: 研究以外のタスク支援（就活、スケジュール管理など）

**注意: Phase 5 は Phase 4 完了後に着手。現時点では設計のみ。**

---

## 5. 現在の環境情報

```yaml
# config.yaml（jarvis-ml-pipeline ルートに配置）
os: Windows 11 Home
python: 3.12.3
venv: C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline\venv
working_dir: C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline

llm:
  primary_provider: gemini
  primary_model: gemini-2.0-flash
  secondary_provider: codex  # 未実装、Phase 2 で追加
  gemini_api_key: SET (環境変数 GEMINI_API_KEY)

codex_cli:
  version: 0.104.0
  auth: ChatGPT Plus OAuth 認証済み

tools:
  git: 2.39.0
  codex: 0.104.0
  zotero: インストール済み

repositories:
  jarvis-ml-pipeline: C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline
  jarvis-desktop: 凍結（触らない）
6. AI への指示テンプレート
新しいチャットセッションを開始する際は、以下を最初に送信すること:

以下の ROADMAP.md を読んでください。
これは私のプロジェクトの設計書です。
あなたはここに書かれた内容に従って作業してください。
現在のフェーズは Phase [N] です。
今日のタスクは [P{N}-{M}] です。

[ROADMAP.md の全文をペースト]
7. 進捗記録
Phase 0
タスク	状態	完了日	メモ
P0-1	未着手		
P0-2	未着手		
P0-3	未着手		
P0-4	未着手		
P0-5	未着手		
Phase 1
タスク	状態	完了日	メモ
P1-1	未着手		
P1-2	未着手		
P1-3	未着手		
P1-4	未着手		
P1-5	未着手		
P1-6	未着手		
Phase 2
タスク	状態	完了日	メモ
P2-1	未着手		
P2-2	未着手		
P2-3	未着手		
P2-4	未着手		
P2-5	未着手		
Phase 3
タスク	状態	完了日	メモ
P3-1	未着手		
P3-2	未着手		
P3-3	未着手		
P3-4	未着手		
P3-5	未着手		
P3-6	未着手		
8. 既知の問題・注意点
google-generativeai が未インストール → P0-1 で解決
Gemini Free Tier のレート制限: ~15 RPM, ~1500 RPD → バッチ処理時は1秒間隔を空けるスリープを入れること
Codex CLI の5時間トークン制限 → 深い分析のみに使い、日常クエリは Gemini に回すこと
sentence-transformers はモデルダウンロードで ~500MB → Phase 1 の D（ハイブリッド検索）で必要になるまで保留
PowerShell スクリプトは必ず UTF-8 BOM 付きで保存
大量の論文を一度に検索すると API レート制限に抵触する → max_results=30 程度に制限し、複数回に分けること
9. 成功の定義（2026年4月1日時点）
以下がすべて達成されていれば Phase 0〜3 は成功:

ターミナルで jarvis search "PD-1 resistance mechanism" と打つと PubMed/arXiv から関連論文が 30 件出てくる
各論文にエビデンスレベル（1a-5）と品質スコアが付いている
上位 10 件のアブストラクトが日本語で要約されている
結果が Markdown ファイルに保存される
BibTeX / RIS でエクスポートでき、Zotero に取り込める
PD-1 主要論文 100 件 + スペルミジン関連 50 件のライブラリがある
本庶先生の主要論文リストがまとまっている
研究領域の勉強ノート 3 本が生成されている
10. 将来ビジョン（参照のみ、現時点では実装しない）
最終的に JARVIS は OpenClaw のようなパーソナル AI アシスタントになる:

チャットインターフェース（Discord / Telegram / LINE）で対話
研究論文の自動監視と新着通知
スケジュール管理、リマインダー
研究ノートの自動整理
実験データの分析支援
論文執筆の下書き支援
就活支援（ES 添削、面接準備）
私生活のタスク管理
これらは Phase 4-5 以降で段階的に実装する。今は Phase 0-3 に集中する。


# AGENTS.md — Codex Operating Rules for jarvis-ml-pipeline

## 0. Repository Purpose
This is a research assistant CLI tool (JARVIS Research OS).
The CLI entry point is `python -m jarvis_cli`.
The core library is `jarvis_core/`.
LLM backend uses `from google import genai` (google-genai package, NOT google.generativeai).

## 1. Environment
- Python 3.12.3, Windows 11, venv
- GEMINI_API_KEY is set and working (Tier 1)
- google-genai package installed (`from google import genai` works)
- No GPU. No Ollama. No OpenAI API key.
- Use only packages already in pyproject.toml or requirements.

## 2. Rules
### Always
- Read existing code before modifying. Use `rg` or `grep` to find related code.
- Keep changes minimal. Fix only what is asked.
- Commit each fix separately with a descriptive message.
- Ensure UTF-8 encoding for all file I/O (especially Japanese text).
- Run `python -m jarvis_cli run --goal "Search 5 papers about PD-1" --category paper_survey` after changes to verify.

### Never
- Add new pip packages without explicit permission.
- Modify LLMClient providers (gemini/ollama/mock) unless asked.
- Do large refactors. Prefer minimal patches.
- Use `import google.generativeai` (deprecated). Use `from google import genai`.
- Touch jarvis-desktop repository (it is frozen).
