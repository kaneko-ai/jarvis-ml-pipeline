# Agent Registry / Router 運用ガイド（実務用）

このファイルは **AgentRegistry と Router をどう設定・運用するか** に限定する。  
アーキテクチャ全体、I/O契約（Task/SubTask/AgentResult）、ログ仕様、ToolGate（ツール乱用抑制）などの設計は正本に集約する。

- 正本：[`docs/JARVIS_MASTER.md`](./JARVIS_MASTER.md)
  - I/O契約：正本「5. AgentのI/Oスキーマ（契約）」
  - ログ仕様：正本「6. ログ（trace）仕様」
  - ツール乱用抑制：正本「7. ツール乱用抑制（ToolGate）」

---

## 1. AgentRegistry の役割
- **設定ファイル（YAML）** で「カテゴリ→利用可能エージェント→デフォルト」を定義する
- 実装と設定を分離し、差し替え（スタブ→実装）を容易にする
- Routerは、Task（または文字列入力）を受け取り、Registryに従ってエージェントを選ぶ

---

## 2. 設定フォーマット（YAML）
エージェント定義は `configs/agents.yaml` に置く。

### 2.1 トップレベルキー
- `agents`：`{ agent_name: agent_definition }`
- `categories`：`{ category_name: category_config }`

### 2.2 agents（エージェント定義）
各エージェントは以下を持つ。
- `category`：論理カテゴリ（例：`paper_survey`, `thesis`, `job_hunting`, `generic`）
- `entrypoint`：`module:ClassName` 形式（例：`jarvis_core.agents:PaperSurveyAgent`）
- `description`：人間向け説明
- `capabilities`：能力タグ（検索、要約、引用監査など）

### 2.3 categories（カテゴリ定義）
- `default_agent`：カテゴリの既定エージェント名
- `agents`：優先順のエージェント候補リスト（上ほど優先）

---

## 3. 設定例（最小）
```yaml
agents:
  PaperSurveyAgent:
    category: paper_survey
    entrypoint: jarvis_core.agents:PaperSurveyAgent
    description: "論文サーベイと要約（まずはスタブでも可）"
    capabilities: ["retrieve", "summarize", "cite"]

  ThesisAgent:
    category: thesis
    entrypoint: jarvis_core.agents:ThesisAgent
    description: "修論文章の整形・校閲・構成支援"
    capabilities: ["rewrite", "structure", "consistency_check"]

categories:
  paper_survey:
    default_agent: PaperSurveyAgent
    agents: [PaperSurveyAgent]

  thesis:
    default_agent: ThesisAgent
    agents: [ThesisAgent]

  generic:
    default_agent: ThesisAgent
    agents: [ThesisAgent]
