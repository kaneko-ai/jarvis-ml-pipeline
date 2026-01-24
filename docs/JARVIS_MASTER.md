# docs/JARVIS_MASTER.md

> Authority: REFERENCE (Level 2, Non-binding)

Last Updated: 2025-12-20
Repo: kaneko-ai/jarvis-ml-pipeline

## 0. この文書の位置づけ（唯一の正本）
本書は Jarvis（javis）の **仕様・設計判断・I/O契約・運用ルール・ロードマップ（M1〜M4）・改修順序**を 1ファイルに集約した「唯一の正本」である。  
**設計の変更は必ず本書を先に更新**し、他docsは本書を参照する。

> 重要：凍結＝機能追加凍結、最小核の実装は進める
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
4) **観測可能性（ログ）必要**：run_id / task_id / subtask_id で JSONL を残す  
5) **内部思考の保存非推奨**：thoughtを成果物・ログに保存避ける（運用を汚染し、後で害になる）

---

## 5. I/O契約（共通スキーマ：将来の実装は必ず準拠）
### 5.1 用語
- Task：ユーザー要求の最上位単位
- SubTask：Taskを実行可能粒度に分割した単位
- Agent：SubTaskを処理する実行主体（薄く保つ）
- Tool：検索・取得・抽出などの外部処理（実体はここに寄せる）
- Validator：品質ゲート（根拠/形式/非推奨事項）

### 5.2 Task（入力：JSON互換）
```json
{
  "task_id": "uuid",
  "title": "CD73に関する最新論文サーベイ",
  "category": "paper_survey",
  "priority": 1,
  "user_goal": "CD73に関する最新論文を調べ、要点を整理してまとめてほしい",
  "constraints": {
    "language": "ja",
    "citation_recommended": true
  },
  "inputs": {
    "query": "CD73",
    "files": [],
    "context_notes": ""
  }
}

### 5.2.1 Task の責務と不変条件（Invariants）
Task は「ユーザー要求を実行可能な単位に正規化した最上位オブジェクト」である。

Task は以下を満たすこと（不変条件）：

task_id はシステムが発行する一意キーであり、同一Taskの再実行でも不変（ログ・再現性のキー）。

user_goal はユーザーの原文またはそれに準ずる要求であり、編集・要約は避ける（監査可能性）。

title はユーザー要求の短い要約で、UI/ログ表示用途。意味は変えないが短縮は許容。

Task が 表さない もの：

実行計画（ステップ順、並列化、リトライ戦略等）は Task 自体には持たせない。

LLMの内部思考や中間推論は Task に保存避ける。

後方互換：

id は task_id の互換プロパティ、goal は title の互換プロパティとして提供するが、外部公開スキーマは task_id/title/user_goal を正とする。

設計注記：将来、再計画（replan）や差分修復（repair）を導入する場合、Taskとは別に ExecutionPlan を導入し、Taskを不変に保つ。

5.3 SubTask（内部：JSON互換）
{
  "subtask_id": "uuid",
  "parent_task_id": "uuid",
  "agent": "PaperFetcherAgent",
  "objective": "CD73に関する関連論文を検索・抽出する",
  "inputs": {
    "query": "CD73"
  },
  "expected_output": {
    "type": "text",
    "schema": {}
  },
  "quality_gates": ["citations_recommended"]
}

### 5.3.1 SubTask の責務と寿命（Lifecycle）
SubTask は「Taskを達成するための実行計画（Plan）の構成要素」である。

SubTask は Task から導出されるが、Taskより可変である（再計画で差し替わり得る）。

Planner の責務：

Task(user_goal) を入力として SubTask 群を生成する。

SubTask の粒度は「Agentが一回で完結できる単位」を目安とする。

Executor/ExecutionEngine の責務：

Plannerが生成した SubTask を順次（または並列）実行する。

失敗時に Planner を再呼び出しして良いが、その場合も Task の user_goal は不変。

5.4 AgentResult（出力：最小スキーマ固定）

重要：thought（内部思考）フィールドは非推奨。
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

### 5.4.1 status の厳密定義
status="success"：要求された出力が生成され、最低限の根拠要件（Citations規約）を満たす。

status="partial"：出力は生成されたが、以下のいずれかに該当する：

要求の一部のみ達成（例：3項目中2項目まで）

根拠不足（Citations規約を満たさない）

外部依存（ネットワーク/レート制限/ソース未取得）により完遂不能

出力はあるが不確実性が高く、利用者に注意喚起が必要

status="fail"：出力生成に失敗、または要求達成の見込みがなく中断。

### 5.4.2 Citations 規約（最低要件）
AgentResult の citations は、回答の検証可能性を担保するための根拠情報である。

最低要件（MVP）：

事実主張（数値・固有名詞・結論）を含む場合、最低1件以上の citation を付与する。

quote は根拠箇所の抜粋であり、過度に長い引用は避ける（短い抜粋に留める）。

locator は機械的に辿れる形式に統一する（例：page:3 / pmid:123... / url:https://...）。

citations が付けられない場合：

status は partial とし、回答本文に「根拠不足」を明示する。

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

6.3 LLMプロバイダー切替（無料運用対応）

Gemini APIの429エラー（レート制限）対策として、LLMバックエンドを切替可能にしている。

| 環境変数 | 説明 | デフォルト |
|----------|------|-----------|
| `LLM_PROVIDER` | `gemini` または `ollama` | `gemini` |
| `GEMINI_API_KEY` | Gemini APIキー（providerがgeminiの場合必要） | - |
| `OLLAMA_BASE_URL` | OllamaサーバーのベースURL | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Ollamaで使用するモデル | `llama3.2` |

**無料運用の推奨設定（Ollama）:**
```bash
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=llama3.2
ollama serve  # 別ターミナルで起動
```

### 6.3.1 Provider 選択の設計注記（将来拡張）

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

M3：Verify（品質ゲート）を仕様化（根拠不足の言い切りを非推奨）

目的：「信用できる出力」を気分ではなく実装で担保する。

DoD

paper_survey と thesis は、根拠が不足する場合「根拠不足/わかりません」を返す

citations必要ルールが validator で強制される

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

PR1は実装済み（ExecutionEngine経由）

---

## 7. 評価（Evals/回帰）

### 7.1 評価の分類
| 種類 | 用途 | 更新頻度 |
|------|------|----------|
| **Frozen** | 回帰テスト用。結果が安定したらPRで"通るべき"テストとして固定 | コミット時 |
| **Live** | 監視用。本番環境で品質劣化を検知 | 実行ごと |

### 7.2 最低限の指標（MVP）
| 指標 | 定義 | 初期しきい値 |
|------|------|--------------|
| `fetch_success_rate` | 論文取得成功率 (取得数/検索ヒット数) | ≥ 0.3 |
| `citation_rate` | 根拠付与率 (citations付き回答/全回答) | ≥ 0.8 |
| `citation_precision` | 引用精度 (正しい引用/全引用) | ≥ 0.9 |
| `claim_precision` | 主張精度 (根拠で支持される主張/全主張) | ≥ 0.85 |
| `unsupported_claim_rate` | 根拠なし主張率 | ≤ 0.1 |
| `failure_repro_rate` | 失敗再現率 (同一入力で同一失敗) | ≥ 0.95 |
| `avg_latency_ms` | 平均レイテンシ | ≤ 30000 |

**方針**: しきい値は「初期は緩く、運用で締める」。品質が安定したら段階的に厳格化。

### 7.3 EvalResult スキーマ（JSON）
```json
{
  "schema_version": "1.0",
  "run_id": "uuid",
  "task_id": "uuid",
  "timestamp": "ISO8601",
  "metrics": {
    "claim_precision": 0.87,
    "citation_precision": 0.92,
    "unsupported_claim_rate": 0.08,
    "avg_latency_ms": 1500
  },
  "thresholds": {
    "claim_precision": 0.85,
    "citation_precision": 0.9,
    "unsupported_claim_rate": 0.1
  },
  "pass_fail": "pass",
  "failing_gates": [],
  "artifacts_path": "logs/runs/{run_id}/eval/"
}
```

### 7.4 Frozen評価セットの運用
- `data/evals/frozen_*.jsonl` に保存
- 各エントリに `task`, `expected_entities`, `min_citations` を持つ
- PRで回帰が出たら **マージ非推奨** (CI gateで強制)

---

## 8. ログ仕様（JSONL）拡張

### 8.1 必要フィールド（拡張版）
```json
{
  "ts": "ISO8601",
  "level": "INFO|WARN|ERROR",
  "run_id": "uuid",
  "trace_id": "uuid",
  "step_id": "int",
  "task_id": "uuid",
  "subtask_id": "uuid|null",
  "event": "PLAN_CREATED|AGENT_SELECTED|TOOL_CALLED|...",
  "event_type": "COGNITIVE|ACTION|COORDINATION",
  "agent": "AgentName|null",
  "tool": "ToolName|null",
  "payload": {}
}
```

### 8.2 event_type (ATS互換)
| event_type | 説明 |
|------------|------|
| `COGNITIVE` | 推論/判断（ただし内部思考そのものは保存非推奨） |
| `ACTION` | 外部ツール呼び出し（検索/API/ファイル操作） |
| `COORDINATION` | タスク管理/計画更新/リトライ |

### 8.3 再現性フィールド（追加）
| フィールド | 説明 |
|-----------|------|
| `prompt_hash` | プロンプトのSHA256ハッシュ（正規化済み） |
| `tool_input_hash` | ツール入力のSHA256ハッシュ |
| `cache_hit` | キャッシュヒット (true/false) |

### 8.4 保存非推奨事項（再掲・明確化）
| 非推奨 | 理由 |
|------|------|
| chain-of-thought全文 | 運用を汚染し、後で害になる |
| 生の推論文 | 監査で問題になる可能性 |
| 長大テキスト | payloadはhashと参照パスで持つ |

**許可**: 要約された理由（短文1-2行）のみ `payload.reason` に入れてよい

---

## 9. CLI + Web（薄いI/O層）

### 9.1 設計原則
- **コアは単一関数**: `jarvis_core.app.run_task(task_dict, run_config_dict) -> (AgentResult, EvalResult)`
- CLI と Web は **同じ入力スキーマ** を受け取り **同じ出力** を返す
- I/O層に業務ロジックを持たせない

### 9.2 CLI仕様
```bash
# タスクファイル指定
python jarvis_cli.py --task-file task.json --out logs/runs/

# 直接指定
python jarvis_cli.py --goal "CD73の最新研究" --category paper_survey
```

### 9.3 Web API仕様（最小）
| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/run` | POST | タスク実行。`{task: {}, run_config: {}}`を受け取り、`{run_id, result}`を返す |
| `/runs/{run_id}` | GET | 保存済み結果を取得 |

**実装優先度**: CLI → Web（Webは後回しでよい）

---

## 10. 取得ポリシー（出版社PDF）

### 10.1 基本方針
- **自動スクレイピングは非推奨**: 出版社サイトへの自動アクセスは行わない
- **正式ルート**: OA（オープンアクセス）+ ユーザー提供PDFのみ

### 10.2 取得元と優先順位
| Adapter | 説明 | 自動化 | デフォルト |
|---------|------|--------|-----------|
| `pmc_oa` | PMC Open Access | ✅ 可 | ✅ 有効 |
| `unpaywall` | Unpaywall OA判定 | ✅ 可 | ✅ 有効 |
| `local_dir` | ユーザー手動取得PDF | - | ✅ 有効 |
| `publisher` | 出版社直接 | ❌ 非推奨 | ❌ 無効 |

### 10.3 取得失敗時の挙動
- 取得できない論文は `partial` 扱い
- `meta.warnings` に理由を記録（例: `"no_oa_available"`, `"pdf_extraction_failed"`）
- **落ちない**: 取得失敗でプロセス全体を止めない

### 10.4 設定例（config.yaml）
```yaml
fetch_adapters:
  - pmc_oa
  - unpaywall
  - local_dir
local_pdf_dir: ~/papers/
```

---

## 11. 最小核の順序（ロードマップ再整理）

**今後の実装順序（最優先から順に）**:
1. **評価** (RP-07): 回帰が走れば品質が追える
2. **観測性** (RP-02): 失敗が追えれば改善できる
3. **再現性** (RP-03): 同じ失敗が再現できれば収束する
4. **実行経路統一** (RP-04-06): ツール層固定、workflow実装
5. **RAG強化** (RP-11): 評価が安定してから
6. **拡張** (M4): 将来機能

---

## 12. リポジトリ衛生（実装前に必ずやるべき運用ルール）

.venv/, __pycache__/, logs/, data/, reports/ は git 管理避ける

依存関係は requirements.txt（またはpyproject）に集約し、再現性を担保する

docsは「正本のみ」が設計変更の入口になる

## 13. 参照（このrepo内の関係）

進捗だけ：docs/codex_progress.md

設定運用：docs/agent_registry.md

概要：docs/jarvis_vision.md

ベースライン：docs/STATE_BASELINE.md

以上。
