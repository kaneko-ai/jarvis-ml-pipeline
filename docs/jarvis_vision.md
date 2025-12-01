# Jarvis Vision / Architecture & Requirements

## 0. 概要

Jarvis は、生命科学研究・修論執筆・文献サーベイ・就職活動を長期的に支援する「研究者向けパーソナルオーケストレーター」である。

このリポジトリ `jarvis-ml-pipeline` は、Jarvis 全体アーキテクチャのうち **Orchestration / Agent 層（Jarvis Core）** を担当する。

Jarvis Core の役割は、

- 人間の自然言語の指示を「機械が実行可能なタスク列」に変換し
- 複数の専門エージェント（文献系、就活系、ニュース系など）を呼び分け
- 結果の品質を自己評価し、必要なら再試行を計画し
- 実行ログと進捗を一元管理する

ことである。

## 1. システム全体像

Jarvis 全体のレイヤ構造は以下の通りとする。

```text
[人間のタスク領域]
  ├─ 修論・論文執筆（CDH13, Ca13Mab）
  ├─ 文献サーベイ・Figure解析
  ├─ 生命科学の勉強（過去問, 霧切テンプレ）
  └─ 就活（ES, 面接, 志望動機 etc.）

        ↓ 人間の指示（自然言語 + 最小限のメタ情報）

[Jarvis UI層]
  ├─ ChatGPT / カスタムGPT（MyGPT）
  ├─ antigravity のチャット
  └─ （将来）統一された「Jarvisダッシュボード」Web UI

        ↓ プロンプト & アクション呼び出し

[Orchestration / Agent層 = Jarvis Core]  ← このリポジトリの担当範囲
  ├─ タスクプランナー（Planner: RobinのPlanner相当）
  ├─ エージェント・レジストリ & ルーター（Crow/Falcon/Finch相当）
  ├─ 実行エンジン（タスクキュー + 実行順制御）
  ├─ 自己評価 & リトライロジック（KamuiOS 的自己評価構造）
  └─ ログ・進捗トラッカー

        ↓ 実際の処理

[ツール / サービス層]  ← 別リポジトリ / 外部サービス
  ├─ 文献系
  │    ├─ paper-fetcher（PubMed/PMC 取得）
  │    ├─ mygpt-paper-analyzer（Next.js + FastAPI + FAISS）
  │    └─ PDF OCR, 図抽出, 要約, RAG
  ├─ 就活・テキスト系
  │    ├─ ES添削/面接質問生成エージェント
  │    └─ 自己PR・研究概要テンプレ生成ツール
  ├─ ニュース・通知系
  │    └─ ニュース要約 → Obsidian 連携の自動化フロー
  └─ （将来）独自ニューラルネット（論文特徴抽出モデルなど）

        ↓ データ入出力

[データ層]
  ├─ 論文PDF（Tohoku VPN + MDX 経由も含む）
  ├─ メタデータ（BibTeX, citation 情報）
  ├─ Embedding / ベクトルDB（FAISS）
  ├─ Obsidian Vault（ノート, 要約）
  └─ GitHub リポジトリ（コードと設定）

2. jarvis-ml-pipeline の責務と非責務
2.1 責務（スコープ内）

自然言語タスクの受け取り

例: 「この PDF 群から CD73 関連の重要 Figure を抽出してランキングして」など

タスクの構造化

「タスクオブジェクト」への正規化（カテゴリ、入力、制約、優先度など）

サブタスク分解（Planning）

例: PDF ダウンロード → OCR → 図抽出 → テキスト要約 → スコアリング

適切なエージェントへのルーティング

文献系エージェント / 就活用エージェント / 勉強用エージェントなど

実行管理

サブタスクの順序制御、依存関係管理、簡易キューイング

自己評価と再試行

「出力が明らかに壊れている / 足りない」場合の再実行や補完タスクの生成

ロギングと進捗管理

後から「何をやったか」を追跡できるログ・メタデータの保存

2.2 非責務（スコープ外）

UI の実装（Web ページ、チャット UI など）

各専門ツールの詳細実装

例: paper-fetcher, mygpt-paper-analyzer 自体の内部ロジック

外部サービス（antigravity, OpenAI API 等）の認証情報の管理

長時間バッチ処理基盤（Kubernetes、ワークフローエンジン本体など）

これらは「Jarvis Core と連携する別コンポーネント」として設計し、本リポジトリでは「どうつなぐか」までを扱う。

3. タスクモデル（抽象仕様）

Jarvis Core が扱う「タスク」は概念的に次のような構造を持つ。

※実装は Python クラスでも Pydantic モデルでもよいが、概念として下記を満たすこと。

{
  "id": "task-uuid-or-hash",
  "category": "paper_survey | thesis | study | job_hunting | generic",
  "goal": "自然言語で書かれた最終目的",
  "inputs": {
    "files": ["path/to/pdf1", "path/to/pdf2"],
    "query": "CD73 AND antibody",
    "context": "修論背景用の文献候補を出したい など"
  },
  "constraints": {
    "max_tokens": 2000,
    "deadline": "2025-01-31T00:00:00",
    "prefer_offline_tools": true
  },
  "priority": "low | normal | high",
  "status": "pending | running | blocked | done | failed",
  "history": [
    // 実行ログ・サブタスクの経過をここに積む想定
  ]
}


必須項目:

goal: 人間が読んでも意味がわかる最終目的

category: 少なくとも paper_survey / thesis / study / job_hunting / generic のいずれか

status: 実行状態

history: 「どのエージェントが何をしたか」を追跡するためのリスト

4. Orchestration / Agent 層のコンポーネント
4.1 Task Planner

責務:

goal と category、inputs をもとに、順序付きサブタスクリストを作る。

サブタスクは少なくとも以下の情報を持つこと。

{
  "id": "subtask-id",
  "parent_task_id": "task-id",
  "step_index": 0,
  "description": "PDF をダウンロードしてローカルに保存する",
  "agent_hint": "paper_fetcher",
  "status": "pending | running | done | failed",
  "result_summary": ""
}


最低限の仕様:

同じカテゴリのタスクに対しては、再利用可能な「典型パターン」を持つこと

例: paper_survey なら「検索 → 絞り込み → 要約 → ランキング」

プランナーのロジックは関数・クラスとして独立させ、テスト可能にすること

4.2 Agent Registry & Router

責務:

利用可能なエージェント（ツール）を「名前」と「能力」で管理する。

例: "paper_fetcher": {"type": "rest_api", "capabilities": ["search_pubmed", "download_pdf"]}

サブタスクの agent_hint や category から、利用すべきエージェントを選ぶ。

最初の段階では、「ダミーエージェント」または「ログだけ出すスタブ」を実装しておき、外部ツールがまだ無くてもパイプラインが動くようにしておく。

4.3 Execution Engine

責務:

サブタスクのステータス管理

順次実行（現時点ではシンプルにシーケンシャルでよい）

失敗したサブタスクの再実行 / スキップの判断

要件:

最初はシングルスレッド・同期処理でよい

将来の非同期化やキューイングを見越し、実行ロジックを 1 箇所に集約する

4.4 Self-Evaluation & Retry Logic

責務:

各サブタスクの出力に対して最低限の検証を行う。

例: 期待されるファイルが存在するか、JSON のスキーマが崩れていないか、など

明らかな失敗の場合に「修正サブタスク」を新規に生成する。

例: 「PDF ダウンロードに失敗 → リトライ回数を変えて再実行するサブタスク」

将来的には LLM を用いた柔らかい評価（「出力の一貫性」「要約の抜け」など）も視野に入れるが、当面は「壊れていないかの検査」が主。

4.5 Logging & Progress Tracking

責務:

タスク / サブタスクの状態変化をすべてログとして記録する。

人間が読める形で「いつ / 何を / どのエージェントが実行したか」を追えるようにする。

実装例:

テキストログ + JSON ログ

logs/ ディレクトリ、またはシンプルな SQLite など

5. 開発ロードマップ（マイルストーン）
M1: 最小 Jarvis Core（CLI ベース）

タスクモデルの実装

Planner の最小実装（カテゴリごとにハードコードでもよい）

ダミーエージェント（ログ出力のみ）の実装

簡易 CLI:

python -m jarvis_core.cli "修論の背景用に○○についてサーベイして" など

M2: 外部ツール連携の骨格

Agent Registry / Router の整理

paper-fetcher / mygpt-paper-analyzer などとのインターフェース層

実際の API 呼び出しは別リポジトリでもよいが、呼び出しフックを定義

設定ファイル（YAML / TOML）でエージェント一覧を管理できるようにする

M3: Self-Evaluation & Retry

実行結果のバリデーション関数群

失敗したサブタスクに対する再試行ポリシー

最大リトライ回数

例外ごとの扱い

M4: UI 層との接続（antigravity / MyGPT）

HTTP API / CLI ラッパー

antigravity の Action から呼び出せる形にする

タスク ID ベースで進捗を問い合わせられる API

6. コーディング規約 / 技術スタック

言語: Python 3.11+（実際の環境に合わせる）

型ヒント: 可能な範囲で typing / pydantic を利用

テスト: pytest

Lint / Format:

ruff or flake8（導入済みであればそれに従う）

black or ruff format

設定値:

.env + 設定ラッパー

API キーなどの秘匿情報はコードに直書きしない

7. 自動コードアシスタント（Codex 等）が触る際のルール

大規模リライトは禁止。小さな変更を積み重ねる。

既存の公開インターフェース（CLI / API 関数のシグネチャ）は、正当な理由なしに破壊しない。

新しい機能を入れる場合は:

まず docs/codex_progress.md に「狙い」「変更範囲」「受け入れ条件」を書く

変更後に「実際に何をしたか」「テスト結果」「残課題」を追記する

Pull Request / ブランチ運用:

codex/* など自動エージェント用ブランチを使う

PR の説明欄に、関連マイルストーン・タスク ID を必ず記載する

このドキュメントは、「人間の開発者」と「自動コードアシスタント」の双方にとっての共通の設計基準である。
実装が進み、Jarvis の実態が変化してきた場合は、この文書を最優先で更新し、常に「現時点の意図」を反映させる。


---

## 2. 上記を前提にした Codex プロンプト（全文）

ブラウザ版 CodeX に投げるタスク本文として、そのまま使える形にしてあります。

```text
あなたは OpenAI Codex (GPT-5.1-Codex-Max) として、GitHub リポジトリ「kaneko-ai/jarvis-ml-pipeline」に対して長時間・自律的に開発を進めるエージェントです。

【最重要の前提】
- このリポジトリは、「Jarvis アーキテクチャ」のうち Orchestration / Agent 層（Jarvis Core）を担当します。
- 全体像とゴールは `docs/jarvis_vision.md` に記載されています。
- まずこのファイルを必ず読み、そのビジョンと整合的な方向にのみリファクタリング・実装・拡張を行ってください。
- 特に、以下の役割を長期的なゴールとして意識してください。
  - タスクプランナー（自然言語の指示 → サブタスク列）
  - 複数エージェントのオーケストレーション（文献系 / 就活系 / ニュース系など）
  - タスク実行結果の自己評価・再実行ロジック
  - ログ・進捗管理（人間が後から追跡しやすい形での記録）

以降の指示（サブタスク分解やエラー解決ループなど）は、すべてこのビジョンを満たすことを優先しつつ実行してください。

【ゴール】
- `docs/jarvis_vision.md` に定義された Jarvis Core の役割に沿って、現在のコードベースを整理・拡張し、
  - タスクモデル
  - Planner
  - Agent Registry / Router
  - Execution Engine
  - Self-Evaluation / Retry Logic
  - Logging / Progress Tracking
  の骨格を段階的に実装します。
- その過程で、エラーが出ないかを実行・テストで確認し、エラーが出た場合は「エラー解決用のサブタスク」を自分で生成して原因究明と修正を行います。
- ある程度まとまった単位ごとに Pull Request（または diff）を作成し、「どこまで終わっていて、何が未完か」が一目でわかる状態にします。

【前提情報の収集（最初に必ず実行する）】
1. リポジトリをクローンし、以下を確認して Jarvis 計画の全体像と現在地を把握してください。
   - `docs/jarvis_vision.md`
   - README や `docs/` 以下の他のドキュメント
   - `PLAN.md`, `ROADMAP.md`, `DESIGN.md` など「計画・設計」に該当しそうなファイル
   - `.github/` 配下の設定・既存 Issues（閲覧できる範囲で）
   - 既存のエージェント構成やディレクトリ構造（例: `jarvis_core/`, `agents/` など）

2. 見つけた情報をもとに、あなたの内部で「高レベル計画一覧」を構成し、リポジトリ直下か `docs/` 配下に
   `docs/codex_progress.md`
   という Markdown ファイルを新規作成または更新して、以下の情報を書き出してください。
   - Jarvis 全体のゴールの要約（あなたの言葉で 5〜10 行）
   - `docs/jarvis_vision.md` に沿ったマイルストーン（M1〜M4）と、その現状（未着手 / 進行中 / 一部完了 / 完了）
   - 各マイルストーンを構成する具体的なサブタスクのリスト（チェックボックス形式）

【ブランチとコミット方針】
- 直接 `main` を書き換えないでください。作業用ブランチの例:
  `codex/jarvis-core-autopilot`
- 1 つのサブタスクごとにコミットを分け、「小さく安全な変更」を積み上げてください。
- ある程度まとまったところで Pull Request を作成し、PR の説明欄に
  - 実施したサブタスク一覧
  - 変更したファイル
  - 実行したテストコマンドと結果
  - 関連マイルストーン（M1〜M4）およびタスク ID
  - 残タスク
  を箇条書きで整理してください。

【メインのループ処理（あなたが自走で繰り返すべきこと）】
Codex 側の制約に達するまで、次のループを自律的に繰り返してください。

1. 「次にやるべきサブタスクの選定」
   - `docs/jarvis_vision.md` のマイルストーン（M1〜M4）と、`docs/codex_progress.md` のチェックリストを見ながら、
     「現状からみて影響範囲が小さく、価値の高いサブタスク」を 1〜3 個選んでください。
   - 例:
     - M1: タスクモデルの最小実装
     - M1: ダミーエージェント + シンプルな Execution Engine
     - M2: Agent Registry のラフな骨格
   - 選んだサブタスクを `docs/codex_progress.md` の「進行中」セクションに明記し、時刻とともにログしてください。

2. 「サブタスクの具体的な設計」
   - 対象となるディレクトリ・モジュール・ファイルを特定してください。
   - そのサブタスクで満たすべき受け入れ条件（Acceptance Criteria）を 3〜5 個、コメントまたは `docs/codex_progress.md` に書いてください。
     例:
     - `Task` モデルが `jarvis_core/task.py` として定義されている
     - 最低限のフィールド（id, category, goal, inputs, status, history）が存在する
     - 単体テスト（例: `tests/test_task_model.py`）が通る
   - なるべく `jarvis_vision.md` の要件から逆算して設計してください。

3. 「実装とリファクタリング」
   - 設計に従ってコードを編集してください。
   - 大規模リライトは避け、既存との互換性を保ちつつ段階的に整理してください。
   - 型ヒント・docstring・コメントが不十分な箇所は、理解のために最低限追加して構いません。

4. 「実行・テストとエラー検知」
   - リポジトリ内の README や `pyproject.toml`, `Makefile` などから、正しい実行／テストコマンドを推論して使用してください。
     例（あくまで例であり、実際にはリポジトリを読んで決めること）:
       - 単体テスト: `pytest` または `python -m pytest`
       - CLI 動作確認: `python -m jarvis_core.cli --help`
   - テストまたは実行中にエラーや例外が発生した場合、それを「エラー解決用サブタスク」として扱ってください。

5. 「エラー解決ループ」
   - エラーを 1 つずつ扱ってください。
   - スタックトレースやログを読み、
     - 原因の仮説
     - 修正方針
     を自分で立て、簡潔に `docs/codex_progress.md` にメモしてください。
   - 必要であればサブタスクの内容を微調整し、コードを修正してから再度テスト・実行を行ってください。
   - 同じエラーについては「原因を特定して修正済み」になるまでこのループを繰り返してください。
   - 外部サービスの認証情報不足など、あなたの側では解決不能な場合は、
     `docs/codex_progress.md` の「ブロック中の課題」セクションに、理由とともに明記してください。

6. 「進捗記録と次ステップ更新」
   - サブタスクが完了したら、`docs/codex_progress.md` の該当項目にチェックを入れ、
     実際に行った変更・実行したテスト・残課題を簡潔に追記してください。
   - M1〜M4 のマイルストーンのうち、完了したもの／取り掛かるべきものを再評価し、
     必要であればマイルストーンやサブタスクのリストを再構成してください。

7. 「PR（または diff）の準備」
   - ある程度まとまった変更がたまったら、作業ブランチから Pull Request を作成してください。
   - PR 説明欄に、今回のループで行ったこと・テスト結果・関連マイルストーン・残タスクを整理し、人間がレビューしやすい状態にしてください。

【制約・注意点】
- セキュリティに関わる処理や認証情報の扱いについては、リポジトリの既存方針に従い、危険な操作やハードコードされた秘密情報の追加は行わないでください。
- 1 回のタスク実行で許されている時間やステップ数に上限がある場合、その範囲内で最大限ループを回し、上限に達した時点で
  - どこまで完了したか
  - 何が未完か
  - 次に人間があなたに投げるべきタスク例
  を `docs/codex_progress.md` と Pull Request 説明欄に明記して終了してください。

# Paper Survey Pipeline Specification (CD73/CDH13-oriented)

## 0. 目的・スコープ
- 修論・論文用の文献サーベイを、Jarvis Core 経由で半自動化する。
- 対象: PubMed / PMC を主とした生命科学論文（当面は CD73 / CDH13 周辺）。

## 1. 入出力仕様 (Interface)

### 1.1 タスク入力 (Task.inputs)
- category: `paper_survey`
- goal: 人間が書く自然言語ゴール
- inputs:
  - query: PubMed クエリ（例: `"NT5E[Title/Abstract] OR CD73[Title/Abstract]"`）
  - date_range: from/to
  - max_results: 上限PMID数
  - filters: open_access, IF、年限など

### 1.2 期待する出力
- structured_result (JSON)
  - papers: [...論文ごとのメタ情報 + メモ...]
  - survey_summary: 修論のどこに効くか（背景/考察）
  - artifacts: 生成された TXT / BibTeX のパス

## 2. パイプライン全体フロー

1. PubMed 検索 (Search)
2. メタデータ取得 (Metadata fetch)
3. PDF / Fulltext 取得 (Fetch)
4. テキスト化 & チャンク (Parse & Chunk)
5. スコアリング / ranking (Rank)
6. サマリー & 出力構造化 (Summarize & Structure)

各ステップについて:
- 入力
- 出力
- 想定する Agent
- 失敗時の挙動（Retry / スキップ条件）

## 3. Jarvis Core との連携ポイント

### 3.1 Planner レベルの定義
- `TaskCategory.PAPER_SURVEY` に対する標準サブタスク列
  - SUBTASK 1: "pubmed_search"
  - SUBTASK 2: "fetch_metadata"
  - SUBTASK 3: "download_fulltext"
  - SUBTASK 4: "parse_and_chunk"
  - SUBTASK 5: "rank_and_filter"
  - SUBTASK 6: "summarize_for_thesis"

### 3.2 Agent Registry 上のエージェント割り当て
- `paper_fetcher` → SUBTASK 1–3 を担当
- `mygpt_paper_analyzer` → SUBTASK 4–6 を担当
- 各エージェントの capabilities をどう定義するか

## 4. Self-Evaluation & Retry のルール

- 例: 「pubmed_search の結果が0件」なら query を緩めて再検索
- 「download_fulltext の成功率が X% 未満」なら、
  - Open Access のみに限定して警告を出す
- JSON schema バリデーション項目

## 5. 実装段階ごとのスコープ

- Phase 1: ダミー実装（外部ツールなしでモックデータを返す）
- Phase 2: paper-fetcher との実接続（PubMed API）
- Phase 3: mygpt-paper-analyzer 連携（解析・ranking）
- Phase 4: 修論テンプレに沿った自動サマリー出力

## 6. 将来拡張

- Tohoku VPN 経由の学内アクセス
- IF / citation に基づく ranking
- 研究テーマごとのテンプレ（CDH13 / CD73 など）


以上の方針に従い、「kaneko-ai/jarvis-ml-pipeline」の Jarvis Core を、`docs/jarvis_vision.md` に沿って段階的かつ安全に育ててください。

