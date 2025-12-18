# JARVIS_MASTER.md
Last Updated: 2025-12-18
Repo: kaneko-ai/jarvis-ml-pipeline

## 0. この文書の目的（CodeX向け）
本書は、Jarvis（javis）の「現在地」「目的地」「設計境界」「実装優先度」「I/O契約」「運用（ログ・評価・安全）」を1ファイルに集約した“正本”である。
CodeX（および将来の開発者）は、まず本書を読み、設計判断と実装の順序を迷わないこと。

---

## 1. 目的地（Jarvisの完成形）
Jarvisは、生命科学研究・修論執筆・文献サーベイ・就職活動を長期的に支援する「研究者向けパーソナル・オーケストレーター」である。

### 1.1 このリポジトリの担当範囲
本repo `jarvis-ml-pipeline` は、Jarvis全体のうち **Orchestration / Agent層（Jarvis Core）** を担当する。
つまり「複数ツール・複数エージェントを束ね、品質と再現性を担保し、運用可能にする司令塔」が責務。

### 1.2 非ゴール（このrepoでやらない）
- 独自LLMの事前学習・新規学習アルゴリズム開発（研究PJとして別管理）
- “モデルそのもの”の最強化を主目的とした寄り道（Jarvis性能は多くの場合、検索・評価・観測可能性がボトルネック）
- OS/VPN/ブラウザ自動化などの高リスク操作を中核機能に据えること（必要なら別層で隔離）

---

## 2. 現在地（zip時点の実装スナップショット）
### 2.1 Jarvis Core（司令塔の骨格）
- `jarvis_core/` に Task / Planner / Router / Registry / Executor / Retry / Validation / Logging の骨格が存在。
- ただし、現状は「部品は揃っているが配線が一貫していない」部分がある（例：CLIがPlanner→Executorの正規ルートを必ず通る設計に統一されていない等）。

### 2.2 文献パイプライン（実務に使える原型）
- `run_pipeline.py`：PubMed検索→メタ取得→PMC OA PDF取得→PDFテキスト化→チャンク化→TF-IDF索引→レポート出力。
- `.github/workflows/paper_update.yml`：Actionsで定期更新し、成果物をartifact化する構造がある。
- `search/`：検索API（FastAPI試作）や簡易サーバ、CLI検索が存在。

### 2.3 重要な構造リスク（放置すると破綻する）
- Core（司令塔）と文献パイプライン（ツール層）が“並走”しており、統合点が曖昧。
- 依存関係（requirements）の網羅性と再現性が弱い可能性がある（実際にimportしているライブラリがrequirementsに未反映になり得る）。
- `.venv/` や `__pycache__/` 等がリポジトリ成果物に混入し得る（容量と差分と再現性の敵）。

---

## 3. 目標アーキテクチャ（境界を明確化する）
### 3.1 レイヤー構造（原則）
- UI層：ChatGPT / MyGPT / antigravity / 将来Dashboard
- Core層：Planner / Router / Executor / Judge / Logger（このrepoの中核）
- Tools/Services層：paper_fetcher、RAG検索、再ランキング、PDF抽出、図抽出、ES支援など（別repo可）
- Data層：PDF、メタ、チャンク、索引、ベクトルDB、Obsidian

### 3.2 Core ↔ Tools の接続ルール
- Coreは「何を・どの順で・どの品質基準で」行うかを決める。
- Toolsは「指定された処理を、決められたI/O契約で」返す。
- CoreはToolsの内部実装に依存しない（API/CLI/関数呼び出しを抽象化）。

---

## 4. 統合後のディレクトリ設計（推奨）
現状の `run_pipeline.py` と `search/` を「Tools層」としてCoreから呼べる形に寄せる。

推奨ツリー（最終形の一例）：

/jarvis_core/ # 司令塔（計画・実行・評価・ログ）
/jarvis_tools/
/paper_pipeline/ # run_pipeline.py相当（取得/抽出/チャンク/索引）
/retrieval/ # keyword+vector+rerank の検索器
/parsers/ # PDF/HTML/画像などの抽出器
/configs/ # agents.yaml, pipeline yaml等
/data/ # 生成物（git管理外推奨）
/reports/ # 生成レポート（git管理外推奨）
/docs/ # 設計・運用（本書を正本に）
/tests/
/scripts/
/.github/workflows/


運用原則：
- `data/` と `reports/` は原則git管理しない（再現はパイプラインで担保）。
- Coreが参照するのは「生成物のパス」と「メタ情報」と「検索API」であり、ファイルの置き場所は設定で切替可能にする。

---

## 5. AgentのI/Oスキーマ（契約）
### 5.1 用語
- Task：ユーザーの要求を表す最上位単位
- SubTask：Taskを実行可能な粒度へ分割したもの
- Agent：SubTaskを処理する専門モジュール
- Tool：Agentが呼び出す外部処理（検索・取得・解析など）
- Judge：品質評価（自己評価、引用妥当性、形式検証など）

### 5.2 共通データ構造（JSON互換）
#### Task（入力）
```json
{
  "task_id": "uuid",
  "title": "string",
  "category": "paper|thesis|job|news|ops|other",
  "priority": 1,
  "user_goal": "string",
  "constraints": {
    "language": "ja",
    "citation_required": true,
    "time_horizon": "short|mid|long"
  },
  "inputs": {
    "query": "string",
    "files": ["path-or-id"],
    "context_notes": "string"
  }
}

SubTask
{
  "subtask_id": "uuid",
  "parent_task_id": "uuid",
  "agent": "AgentName",
  "objective": "string",
  "inputs": { "any": "json" },
  "expected_output": {
    "type": "text|json|files",
    "schema": { "any": "json" }
  },
  "quality_gates": ["gate_id_1", "gate_id_2"]
}

AgentResult（出力）
{
  "status": "success|fail|partial",
  "summary": "string",
  "outputs": { "any": "json" },
  "artifacts": [
    { "type": "file|dataset|index", "path": "string", "desc": "string" }
  ],
  "metrics": {
    "latency_ms": 0,
    "tool_calls": 0,
    "tokens_in": 0,
    "tokens_out": 0
  },
  "citations": [
    { "source": "string", "locator": "string", "note": "string" }
  ],
  "warnings": ["string"],
  "next_actions": ["string"]
}

6. ログ（trace）仕様（観測可能性を“必須要件”にする）

方針：後から「何が起きたか」を再構成できないシステムは運用不能。ログは贅沢品ではなく仕様。

6.1 形式

JSONL（1行1イベント）

すべての実行に run_id、すべてのタスクに task_id、すべてのサブタスクに subtask_id

すべてのツール呼び出しに tool_call_id と入出力ハッシュ

6.2 Eventスキーマ（例）
{
  "ts": "2025-12-18T12:00:00+09:00",
  "level": "INFO|WARN|ERROR",
  "run_id": "uuid",
  "task_id": "uuid",
  "subtask_id": "uuid",
  "event": "PLAN_CREATED|AGENT_SELECTED|TOOL_CALLED|TOOL_RETURNED|JUDGE_PASSED|JUDGE_FAILED|RETRY|DONE",
  "agent": "AgentName",
  "tool": "ToolName",
  "input_hash": "sha256",
  "output_hash": "sha256",
  "payload": { "any": "json" }
}

6.3 最低限取るべきメトリクス

サブタスク別：所要時間、失敗率、リトライ回数、ツール呼び出し回数

出力品質：Judgeスコア、引用不足フラグ、形式不正フラグ

コスト：tokens_in/out（LLM依存なら）

7. ツール乱用抑制（Tool Overuse Mitigation：必須）

ツールが増えるほど、無駄呼び出しがコスト・遅延・破綻要因になる。
原則：まず内部推論で足りるか判定し、足りない場合のみ最小ツールを選ぶ。

7.1 ToolGate（疑似仕様）

入力：SubTask + 現在のコンテキスト

出力：use_tool: yes/no と tool_candidates[] と reason

ルール：

既にローカル索引に答えがあるなら外部検索しない

引用必須タスクで根拠が不足なら検索を許可

高コストツールは段階承認（rerank→全文取得の順）

8. RAGをModular化する最小分割案（いまのTF-IDFを進化させる道筋）
8.1 最小モジュール（段階導入）

Ingest（取得）

Parse（テキスト化）

Chunk（チャンク化：まずはフラット、次に階層）

Index（keyword + vector）

Retrieve（候補取得）

Rerank（並べ替え：軽量→高精度へ）

BuildContext（文脈構成：重複排除、章節優先）

Generate（要約/回答）

Judge（妥当性/引用/形式チェック）

Report（最終整形）

8.2 階層チャンク（論文・修論に効く）

doc_id, section, subsection, paragraph_id, page, figure_ref をメタに持つ

目的：検索精度だけでなく、説明可能性（なぜその根拠か）を上げる

8.3 ハイブリッド検索（最短で効く）

keyword（TF-IDF/BM25相当） + embedding（意味検索）を足し算

その上で reranker を挟む（上位20→上位5に絞る等）

9. マイルストーン（M1–M4）定義（Done条件を明文化）
M1: Minimal Core

Done条件：

CLI/APIが必ず Planner→Executor→Router の正規ルートを通る

Task→SubTask→AgentResult が一貫したI/Oで流れる

JSONLログが残る

M2: Tool統合（文献）

Done条件：

Paper系Agentが paper_pipeline を呼び出し、索引更新→検索→要約まで通る

成果物パスとメタがAgentResultに載る

M3: 自己評価と再試行

Done条件：

Judgeが最低2種類（形式＋引用/整合）あり、失敗時にリトライ方針が動く

リトライの理由がログに残る

M4: UI/API接続

Done条件：

/run と /status/{run_id} があり、外部UIから進捗参照可能

実行結果を“最終報告フォーマット”で返す

10. 直近の実装優先順位（最短で強くする）

優先度A（今すぐ）：

Coreの配線統一：CLI/APIは正規ルート固定（Planner→Executor→Router）

Tools層の明確化：run_pipeline.py と search/ を jarvis_tools/ に寄せる（またはAgentとして接続点を作る）

ログJSONL：run_id/task_id/subtask_idの一貫性を最優先

優先度B（次）：
4) 階層メタ付きチャンク
5) ハイブリッド検索 + rerank
6) ToolGate導入（無駄ツール呼び出し抑制）

優先度C（余力）：
7) ワークフロー自動生成（候補生成→実行→judge→採用の小さな探索）
8) 画像/図の評価自動化（必要になってから）

11. 参照資料（設計の出典として扱う候補）

Retrieval-Augmented Generation for Large Language Models: A Survey

BookRAG: Hierarchical Structure-aware Index-based RAG for Complex Documents

AgentOps: Observability of LLM Agents

SMART: Tool Overuse Mitigation

AGAPI: Agentic AI Platform / 多API統合設計

その他（あなたが添付した資料一式）

本書は、それらの“思想”をJarvisの要件へ落とすための実装仕様である。

12. 既存docsとの関係（移行方針）

docs/jarvis_vision.md：本書への参照リンクだけ残し、重複は削る（正本は本書）

docs/codex_progress.md：マイルストーンのチェックリスト（本書のM1–M4に整合させる）

docs/agent_registry.md：agents.yamlの書き方・運用手順（本書のI/O契約に合わせる）

以上。


---
