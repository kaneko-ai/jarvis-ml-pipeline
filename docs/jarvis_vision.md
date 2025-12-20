
# Jarvis Vision（正本）
Last Updated: 2025-12-20

このファイルは本リポジトリにおける **Jarvis（javis）の正本（Master）** である。  
設計・仕様・運用ルールの「正」は必ずここに集約する。

---

## 1. システム全体像（レイヤ構造）

```text
[UI層]
  ChatGPT / MyGPT / antigravity / 将来Dashboard

        ↓（自然言語 + 最小メタ）

[Jarvis Core（このrepoの担当範囲）]
  Planner
    → Router / Registry
      → Execution
        → Validation / Retry
          → Logging / Progress

        ↓（疎結合）

[Tools / Services層]
  paper_pipeline
  retrieval（keyword + vector + rerank）
  mygpt-paper-analyzer
  OCR / 図抽出 / ES支援 / ニュース監視

        ↓

[データ層]
  PDF / BibTeX / citation
  チャンク / 索引 / ベクトルDB
  Obsidian Vault
  GitHub（コード・設定）
2. jarvis-ml-pipeline の責務と非責務
2.1 責務（スコープ内）
自然言語タスクを Task として受け取る

Task を SubTask に分解する（Planner）

Agent を選択する（Registry / Router）

SubTask を順次実行する（Execution）

妥当性検証・再試行を行う（Validation / Retry）

実行を再現可能な形で記録する（Logging）

2.2 非責務（スコープ外）
UI 実装

独自 LLM の事前学習・研究

高リスクな自動操作の中核化

3. Task モデル（抽象仕様）
json
コードをコピーする
{
  "id": "task-id",
  "category": "paper_survey | thesis | study | job_hunting | generic",
  "goal": "自然言語の目的",
  "inputs": {
    "query": "string",
    "files": [],
    "context": "string"
  },
  "constraints": {
    "language": "ja",
    "citation_required": true
  },
  "priority": 1,
  "status": "pending | running | done | failed",
  "history": []
}
4. Orchestration / Agent 層
4.1 Planner
Task を順序付き SubTask に分解する

4.2 Registry / Router
YAML 定義に基づき Agent を選択する

4.3 Execution
SubTask を逐次実行する

4.4 Validation / Retry
出力の最低限の妥当性を保証する

4.5 Logging
run_id / task_id / subtask_id を JSONL で記録する

5. マイルストーン
M1
CLI が Planner → Execution → Router 経路で動作

M2
外部ツール（paper_pipeline 等）を Agent 経由で呼べる

M3
Self-Evaluation / Retry が動作

M4
UI（antigravity / MyGPT）と接続

6. CodeX 用プロンプト
text
コードをコピーする
あなたは Jarvis Core を改善するエンジニアです。
正本仕様は docs/jarvis_vision.md にあります。
仕様を最優先し、小さな変更で改善してください。
yaml
コードをコピーする

---

# ② `docs/codex_progress.md`  
👉 **このコードブロックを「全部」コピーして置き換え**

```markdown
# Codex Progress
Last Updated: 2025-12-20

このファイルは進捗のみを管理する。

---

## Milestones

- M1: Minimal Core — 部分完了
- M2: Tool Integration — 未完了
- M3: Self-Evaluation — 未完了
- M4: UI Integration — 未着手

---

## M1
- [x] Task モデル
- [x] Registry / Router
- [ ] CLI 正規経路（Planner → Execution）

## M2
- [ ] paper_survey E2E（スタブ可）
- [ ] artifacts 出力

## M3
- [ ] Judge 実装
- [ ] Retry 方針

## M4
- [ ] /run API
- [ ] /status API
③ docs/agent_registry.md
👉 このコードブロックを「全部」コピーして置き換え

markdown
コードをコピーする
# Agent Registry / Router Guide
Last Updated: 2025-12-20

本ファイルは AgentRegistry と Router の運用ルールのみを扱う。

---

## 設定ファイル（configs/agents.yaml）

```yaml
agents:
  PaperSurveyAgent:
    category: paper_survey
    entrypoint: jarvis_core.agents:PaperSurveyAgent
    capabilities: [retrieve, summarize, cite]

categories:
  paper_survey:
    default_agent: PaperSurveyAgent
    agents: [PaperSurveyAgent]
Router の基本動作
Task.category を優先

default_agent を使用

文字列入力は暫定的に generic 扱い

注意点
設定で差し替え可能性を維持する

ログなしの分岐は作らない

yaml
コードをコピーする

---

# あなたがやること（これだけ）

1. `docs/jarvis_vision.md` を開く  
2. **中身を全部削除**  
3. ①のコードブロックを **最初から最後までコピーして貼り付け**  
4. 同様に ②、③ をそれぞれ対応するファイルに貼る  

以上です。

---







