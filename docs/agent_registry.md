# docs/agent_registry.md
Last Updated: 2025-12-20

## 0. この文書の位置づけ
本書は **AgentRegistry と Router をどう設定・運用するか**に限定する。  
I/O契約、ログ仕様、ロードマップは正本に集約する。

- 正本：`docs/JARVIS_MASTER.md`

---

## 1. 基本方針（甘さなし）
- Agentは薄く保つ（役割を増やしすぎない）
- 実体は Tool に寄せる（検索・取得・抽出は tools で実装する）
- 設定（YAML）を壊さない（`...` や未完の断片を混入させない）
- 入口の分岐は必ずログを残す（原因追跡不能な分岐は禁止）

---

## 2. 設定ファイル（configs/agents.yaml）
### 2.1 トップレベル
- `agents`：`{ agent_name: agent_definition }`
- `categories`：`{ category_name: category_config }`

### 2.2 agents（エージェント定義）
各エージェントは以下を持つ。
- `category`：論理カテゴリ（`paper_survey`, `thesis`, `job_hunting`, `generic`）
- `entrypoint`：`module:ClassName` 形式（例：`jarvis_core.agents:ThesisAgent`）
- `description`：人間向け説明
- `capabilities`：能力タグ（将来のルーティング補助。まずは飾りでよい）

### 2.3 categories（カテゴリ定義）
- `default_agent`：カテゴリ既定エージェント
- `agents`：候補リスト（上ほど優先）

---

## 3. 最小の推奨設定例
※ 実際の `configs/agents.yaml` はリポジトリに合わせて調整する。  
ここでは「壊れない最小例」を示す。

```yaml
agents:
  thesis:
    category: thesis
    description: "Thesis writing assistant"
    entrypoint: "jarvis_core.agents:ThesisAgent"
    capabilities: ["rewrite", "structure"]

  paper_fetcher:
    category: paper_survey
    description: "Paper survey agent (must return citations)"
    entrypoint: "jarvis_core.agents:PaperFetcherAgent"
    capabilities: ["retrieve", "summarize", "cite"]

  es_edit:
    category: job_hunting
    description: "Entry sheet editing agent"
    entrypoint: "jarvis_core.agents:ESEditAgent"
    capabilities: ["rewrite"]

  misc:
    category: generic
    description: "Generic fallback agent"
    entrypoint: "jarvis_core.agents:MiscAgent"
    capabilities: ["generic_answer"]

categories:
  paper_survey:
    default_agent: paper_fetcher
    agents: [paper_fetcher]

  thesis:
    default_agent: thesis
    agents: [thesis]

  job_hunting:
    default_agent: es_edit
    agents: [es_edit]

  generic:
    default_agent: misc
    agents: [misc]
4. Router運用ルール（最低限）
Task.category を最優先する（曖昧な分類より優先）

category未指定の文字列入力は generic として扱う（過剰な推測分類はしない）

paper_survey は原則として retrieval tool を使用し、citations を伴わない言い切りを禁止する（正本の品質規約に準拠）

5. 破綻パターン（避ける）
YAMLに未完断片を混ぜる（ロード不能・運用不能）

Agentに責務を詰め込む（テスト不能・保守不能）

“実行はしたがログがない”分岐を作る（原因特定不能）

以上。

makefile
コードをコピーする
::contentReference[oaicite:0]{index=0}
