# docs/JARVIS_MASTER.md
Last Updated: 2025-12-20
Repo: kaneko-ai/jarvis-ml-pipeline

## 0. この文書の位置づけ（唯一の正本）
本書は Jarvis（javis）の **仕様・設計判断・I/O契約・運用ルール・ロードマップ（M1〜M4）・改修順序**を 1ファイルに集約した「唯一の正本」である。  
**設計の変更は必ず本書を先に更新**し、他docsは本書を参照する。

> 重要：現時点では「実装を進めない」前提で、計画を詳細に固定する。  
> したがって本書は「実装メモ」ではなく「将来の実装を迷わせない設計仕様書」である。

---

## 1. 目的地（Jarvisの完成形：このrepoの担当範囲）
Jarvisは、生命科学研究・修論執筆・文献サーベイ・就職活動を長期的に支援する「研究者向けパーソナル・オーケストレーター」である。

本repo `jarvis-ml-pipeline` の責務は **Orchestration / Agent層（Jarvis Core）** と、当面は同居している **文献パイプライン（run_pipeline / 検索）**を、将来の拡張に耐える形へ整理し、運用可能な“核”として固定すること。

---

## 2. 現在地（添付zip時点の事実）
### 2.1 Jarvis Core（骨格はある）
- `jarvis_core/` に Task / Planner / Router / Registry / Executor / Retry / Validation / Logging の骨格が存在。
- ただし **実行経路（入口→計画→実行→検証→保存）が統一されていない**懸念がある（設計はあるが、経路が固定されていない）。

### 2.2 文献パイプライン（実務価値が高い資産）
- `run_pipeline.py`：PubMed検索→メタ取得→（可能なら）PDF取得→PDFテキスト化→チャンク化→TF-IDF索引→レポート出力。
- `search_index.py` / `search/`：索引検索（CLI）や簡易API（FastAPI）試作。

### 2.3 放置すると確実に破綻する構造リスク
- Core（司令塔）と文献パイプライン（ツール層）が「並走」し、統合点が曖昧なまま機能追加すると、運用不能になる。
- 出力の品質保証（根拠・引用・不確実性表記）が仕様として固定されていないと、結果が信用できず手戻りが増える。

---

## 3. 今回の意思決定（スコープ凍結）
以下は **当面作らない（凍結）**。議論の余地なく、ロードマップから外す。

- Web UI（`/run` と `/status`）
- PDF→スライド自動生成（MVidEra系）
- Podcast生成
- PDF→動画
- GitHub Actions定期実行の強化（失敗通知/差分要約/Slack等）
- LoRAでの専用モデル化
- セキュリティ自動監査（BugTrace系）

理由：現状の最大課題は「機能不足」ではなく **中核の配線と品質ゲート不在**であり、ここを先に固めない限り、追加機能はすべて負債化するため。

---

## 4. 目標アーキテクチャ（最小核）
### 4.1 レイヤ（最小）
- Interface：CLI（まずここだけ）
- Core：Plan → Act → Verify → Store（本repoの核）
- Tools：文献パイプライン（索引更新/検索/抽出）を“道具”として呼べること
- Data：PDF/メタ/チャンク/索引/レポート（原則git管理外）

### 4.2 “核”の非交渉原則（設計規約）
1) **実行経路の強制**：入口は必ず Plan→Act→Verify→Store を通る  
2) **根拠優先**：根拠（チャンク等）が不足する場合、言い切らない（「根拠不足」「わかりません」）  
3) **出力スキーマ固定**：成果物は統一スキーマで返す（後述）  
4) **観測可能性（ログ）必須**：run_id / task_id / subtask_id で JSONL を残す  
5) **内部思考の保存禁止**：thoughtを成果物・ログに保存しない（運用を汚染し、後で害になる）

---

## 5. I/O契約（共通スキーマ：将来の実装は必ず準拠）
### 5.1 用語
- Task：ユーザー要求の最上位単位
- SubTask：Taskを実行可能粒度に分割した単位
- Agent：SubTaskを処理する実行主体（薄く保つ）
- Tool：検索・取得・抽出などの外部処理（実体はここに寄せる）
- Validator：品質ゲート（根拠/形式/禁止事項）

### 5.2 Task（入力：JSON互換）
```json
{
  "task_id": "uuid",
  "title": "string",
  "category": "paper_survey|thesis|job_hunting|generic",
  "priority": 1,
  "user_goal": "string",
  "constraints": {
    "language": "ja",
    "citation_required": true
  },
  "inputs": {
    "query": "string",
    "files": ["path-or-id"],
    "context_notes": "string"
  }
}

5.3 SubTask（内部：JSON互換）
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

5.4 AgentResult（出力：最小スキーマ固定）

重要：thought（内部思考）フィールドは禁止。
代わりに「根拠」「推測」を分離し、推測は推測と明記する。

{
  "status": "success|fail|partial",
  "answer": "string",
  "citations": [
    {
      "chunk_id": "string",
      "source": "string",
      "locator": "page:3|pmid:...|url:...",
      "quote": "string"
    }
  ],
  "meta": {
    "retrieval": {
      "index_path": "string",
      "query_used": "string",
      "top_k": 5,
      "hits": 5
    },
    "warnings": ["string"]
  }
}

6. ログ仕様（運用要件：JSONL）

方針：後から「何が起きたか」を再構成できないシステムは運用不能。ログは仕様。

6.1 形式

JSONL（1行1イベント）

すべての実行に run_id、すべてのタスクに task_id、すべてのサブタスクに subtask_id

6.2 Event例
{
  "ts": "2025-12-20T12:00:00+09:00",
  "level": "INFO|WARN|ERROR",
  "run_id": "uuid",
  "task_id": "uuid",
  "subtask_id": "uuid",
  "event": "PLAN_CREATED|AGENT_SELECTED|TOOL_CALLED|TOOL_RETURNED|VALIDATION_PASSED|VALIDATION_FAILED|RETRY|DONE",
  "agent": "AgentName",
  "tool": "ToolName",
  "payload": { "any": "json" }
}

7. 新ロードマップ（M1〜M4：作り直し版）

注意：ここでの M1〜M4 は「今後の実装計画」であり、現時点では未着手でよい。
ただし 完了条件（DoD）と改修順序は先に固定する。

M1：実行経路の統一（Plan→Act→Verify→Store の配線を強制）

目的：入口が Router直行する等の揺らぎを排除し、Coreの“核”を固定する。

DoD

CLI（または run_jarvis()）が必ず ExecutionEngine を通る

全実行で JSONLログ（run_id）が残る

出力が 5.4 の AgentResult 最小スキーマに収束する

thought保存なし

改修順序（ファイル単位：計画）

jarvis_core/__init__.py：run_jarvis() を ExecutionEngine 経由にする

jarvis_core/cli.py：入口を一本化（config受け取り、run_id表示）

jarvis_core/executor.py：最終結果を必ず返す（finalizerを置く）

jarvis_core/agents.py：thought依存を排除し、answer/citations/metaに収束

tests/*：DummyLLM返却と期待値をスキーマに合わせて修正

M2：文献パイプラインを“ツール化”し、Paper系タスクで必ず使える状態にする

目的：run_pipeline.py と索引検索を、LLM（Agent）から道具として呼ぶ。

DoD

paper_survey で「ローカル索引検索→根拠（citations）→要約」が一気通貫

検索結果は chunk_id/source/locator/text で取り回せる

PaperFetcherAgent がスタブでなくなる（最低限のE2E）

改修順序（計画）

新規 jarvis_core/tools/：検索とパイプライン呼び出しを関数化

search_index.py：ロジックを tools に移植し、スクリプトは薄いラッパにする

jarvis_core/agents.py：PaperFetcherAgentで retrieval tool を呼び、citationsを付ける

jarvis_core/planner.py：paper_survey手順を現実的に更新（検索→抽出→要約）

M3：Verify（品質ゲート）を仕様化（根拠不足の言い切りを禁止）

目的：「信用できる出力」を気分ではなく実装で担保する。

DoD

paper_survey と thesis は、根拠が不足する場合「根拠不足/わかりません」を返す

citations必須ルールが validator で強制される

失敗理由がログに残る（例：missing_citations / no_hits）

改修順序（計画）

jarvis_core/validation.py：CitationValidator（最小）を実装

jarvis_core/executor.py：validation失敗時の挙動（fail/partial/retry）を固定

tests/*：根拠不足で fail/partial になるテストを追加

M4：拡張可能な構造へ整形（Skill中心への地ならし＋docsの一本化）

目的：将来、機能を増やす場所を固定し、迷子とスパゲティ化を防ぐ。

DoD

機能追加は原則 jarvis_core/tools/ と configs/ の追加で完結する

docsが一本化され、他docsは正本への参照のみになる（重複排除）

最短の使用例（examples）が存在し、再現可能に動く

改修順序（計画）

docs/jarvis_vision.md：正本を名乗らせず「概要」に落とす

docs/agent_registry.md：スキーマと運用規約を本書に整合

docs/codex_progress.md：M1〜M4（新定義）に合わせて更新

（任意）examples/：paper_survey最短導線の例を追加

8. リポジトリ衛生（実装前に必ずやるべき運用ルール）

.venv/, __pycache__/, logs/, data/, reports/ は git 管理しない

依存関係は requirements.txt（またはpyproject）に集約し、再現性を担保する

docsは「正本のみ」が設計変更の入口になる

9. 参照（このrepo内の関係）

進捗だけ：docs/codex_progress.md

設定運用：docs/agent_registry.md

概要：docs/jarvis_vision.md

以上。
