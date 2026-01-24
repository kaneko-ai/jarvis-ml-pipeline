# STATE BASELINE v1.0

> Authority: REFERENCE (Level 2, Non-binding)


現状のJARVIS Research OSの実行経路・I/O契約を"事実"として整理したドキュメント。

## 1. 主要エントリポイント

### main.py
- **責務**: 対話式CLIエントリポイント
- **処理**: stdin から複数行入力 → `run_jarvis(task)` 呼び出し → 回答出力
- **I/O**: stdin(対話) → stdout(回答)
- **依存**: `jarvis_core.run_jarvis`

### jarvis_core/__init__.py
- **責務**: パッケージ公開API
- **公開関数**: `run_jarvis(goal, category)` - 唯一の高レベル実行関数
- **処理**: Task生成 → ExecutionEngine起動 → AgentResult取得 → answer返却
- **I/O**: goal文字列 → answer文字列

### jarvis_core/executor.py
- **責務**: タスクのプラン→実行→検証オーケストレーション
- **クラス**: `ExecutionEngine`
- **主要メソッド**:
  - `run(root_task)`: プラン→サブタスク実行
  - `run_and_get_answer(root_task)`: 便利ラッパー
  - `_normalize_agent_result()`: ステータス正規化
  - `_validate_citations()`: 引用検証
  - `_execute_with_retry()`: リトライ付き実行

### run_pipeline.py
- **責務**: 文献取得→PDF抽出→チャンク→TF-IDF索引のバッチパイプライン
- **処理ステップ**:
  1. `pubmed_esearch()` - PubMed検索
  2. `pubmed_esummary()` - メタデータ取得
  3. `download_pmc_pdfs()` - PMC OA PDF取得
  4. `pdf_to_text()` - テキスト抽出
  5. `split_into_chunks()` - チャンク分割
  6. `build_index()` - TF-IDF索引構築
  7. `generate_report()` - Markdownレポート生成
- **I/O**: config.yaml → data/{raw,processed,index,reports}
- **外部依存**: PubMed API, PMC OA FTPサーバー

### search/
- **責務**: TF-IDF索引を使った検索CLI・API
- **ファイル**:
  - `search_cd73.py` - CD73関連検索CLI
  - `search_cd13.py` - CD13関連検索CLI
  - `api_cd73.py` - 検索API
  - `cd73_server.py` - 検索サーバー
- **I/O**: クエリ文字列 → 検索結果JSON/表示

---

## 2. 実行経路図（ASCII）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        JARVIS Research OS v4.2                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [main.py]                           [run_pipeline.py]                       │
│      │                                     │                                 │
│      ▼                                     ▼                                 │
│  stdin(対話入力)                      config.yaml                            │
│      │                                     │                                 │
│      ▼                                     ▼                                 │
│ ┌────────────────────┐           ┌─────────────────────┐                    │
│ │  run_jarvis()      │           │  run_pipeline()     │                    │
│ │  jarvis_core/      │           │  (スタンドアロン)    │                    │
│ └────────────────────┘           └─────────────────────┘                    │
│      │                                     │                                 │
│      ▼                                     ▼                                 │
│ ┌────────────────────┐           ┌─────────────────────┐                    │
│ │ ExecutionEngine    │           │ PubMed API          │                    │
│ │   .run()           │           │ PMC OA Service      │                    │
│ └────────────────────┘           └─────────────────────┘                    │
│      │                                     │                                 │
│      ├──────────────┐                      ▼                                 │
│      ▼              ▼              ┌───────────────────┐                    │
│ ┌─────────┐  ┌───────────┐         │ PDF → chunks.jsonl│                    │
│ │ Planner │  │ Router    │         │ → tfidf_index.pkl │                    │
│ └─────────┘  └───────────┘         └───────────────────┘                    │
│      │              │                      │                                 │
│      ▼              ▼                      ▼                                 │
│ ┌─────────┐  ┌───────────────┐     ┌───────────────────┐                    │
│ │ SubTask │  │ Agent選択     │     │ search/* CLI/API  │                    │
│ │ 生成    │  │ (PaperFetcher │     │ TF-IDF検索        │                    │
│ └─────────┘  │  等)          │     └───────────────────┘                    │
│              └───────────────┘                                              │
│                    │                                                         │
│                    ▼                                                         │
│              ┌───────────────┐                                              │
│              │ LLMClient     │                                              │
│              │ (gemini-2.0)  │                                              │
│              └───────────────┘                                              │
│                    │                                                         │
│                    ▼                                                         │
│              ┌───────────────┐                                              │
│              │ AgentResult   │                                              │
│              │ (answer+      │                                              │
│              │  citations)   │                                              │
│              └───────────────┘                                              │
│                    │                                                         │
│                    ▼                                                         │
│              ┌───────────────┐                                              │
│              │ validate_     │                                              │
│              │ citations()   │                                              │
│              └───────────────┘                                              │
│                    │                                                         │
│                    ▼                                                         │
│              stdout(回答)                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 命令→計画→実行→検証→保存 の詳細経路

```
[命令]  main.py stdin
           │
           ▼
[Task生成] Task(goal, category)
           │
           ▼
[計画]  Planner.plan(root_task)
           │
           ├─→ decompose() サブタスク分割
           │
           ▼
[Agent選択] Router.select_agent(subtask)
           │
           ├─→ category判定 → PaperFetcherAgent / ResearchAgent / 他
           │
           ▼
[実行]  Agent.run(task)
           │
           ├─→ LLMClient.generate()
           │
           ▼
[検証]  ExecutionEngine._normalize_agent_result()
        ExecutionEngine._validate_citations()
        ExecutionEngine._check_citation_relevance()
           │
           ├─→ status: complete / partial / failed
           ├─→ warnings 収集
           │
           ▼
[保存]  (現状は明示的な永続化なし - メモリ上のみ)
           │
           ▼
[出力]  stdout(answer)
```

---

## 4. 未接続・Stub箇所（事実）

| 箇所 | 現状 | 備考 |
|------|------|------|
| `PaperFetcherAgent` | stub実装 | `run_pipeline.py`と未接続。TF-IDF索引を参照していない |
| `run_pipeline.py` ↔ `jarvis_core` | **並走** | 互いに独立。Core側がpipelineの成果物を使っていない |
| Telemetry/ログ | **未実装** | run_id/trace_id/step_idの構造化ログがない |
| キャッシュ | **未実装** | tool呼び出しのキャッシュなし。再現性確保できず |
| 評価 | **未統合** | `jarvis_core/eval`は存在するがCI連携なし |
| Provenance | locator不足 | チャンクに page/span 情報が不十分 |

---

## 5. I/O契約（現状）

### run_jarvis()
```python
def run_jarvis(goal: str, category: str = "generic") -> str:
    """
    入力: goal(文字列), category(enum文字列)
    出力: answer(文字列)
    副作用: なし（ログファイル生成なし）
    """
```

### ExecutionEngine.run()
```python
def run(self, root_task: Task) -> List[Task]:
    """
    入力: Task
    出力: 実行済みSubTask列
    副作用: EvidenceStore更新（メモリ上）
    """
```

### AgentResult（期待構造）
```json
{
  "status": "complete | partial | failed",
  "answer": "string",
  "citations": [
    {
      "chunk_id": "string",
      "source": "string",
      "locator": "string (例: pmid:12345 page:3)",
      "text": "string"
    }
  ],
  "warnings": ["string"]
}
```

---

## 6. 次ステップのための基準

このドキュメントを基準として、以下のPRでの変更を評価する:

- RP-01: 仕様更新 → JARVIS_MASTER.md に評価/ログ/CLI/取得ポリシーを追加
- RP-02: 観測性 → Telemetryパッケージ追加、events.jsonl生成
- RP-03: 再現性 → キャッシュ+リプレイ実装
- RP-04: ツール層分離 → jarvis_tools/papers/ へ移植
- RP-05: Provenance → locator/page/spanを必要化
- RP-06: 中核ワークフロー → paper_survey workflow実装

---

## 7. テストベースライン（PR-60）

```yaml
# PR-60: Core test collection baseline
core_test_collected: 99
baseline_date: 2024-12-21
```

---

*Generated: 2024-12-21*

