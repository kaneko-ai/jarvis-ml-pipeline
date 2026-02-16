> Authority: SPEC (Level 1, Binding)

# JARVIS Research OS
# MASTER_SPEC.md v1.2

> **強制文書**: 本仕様書は全実装の最上位規約

---

## 0. 基本原則（非交渉）

### 実行入口（唯一）

| 入口 | ファイル | 用途 |
|------|----------|------|
| **CLI（唯一）** | `jarvis_cli.py` | すべての実行はここから |
| デモ | `main.py` | 開発デモ専用（本番禁止） |

> **警告**: jarvis_cli.py 以外からの実行は禁止

### 成果物契約（必須10ファイル）

> DEC-006により唯一の成果物契約として確定

すべてのrunは `logs/runs/{run_id}/` に以下のファイルを**必ず**生成する:

| ファイル | 用途 | 必須キー |
|----------|------|----------|
| `input.json` | 実行条件 | goal, query, constraints |
| `run_config.json` | 実行設定 | run_id, pipeline, timestamp |
| `papers.jsonl` | 論文メタ | paper_id, title, year |
| `claims.jsonl` | 主張 | claim_id, paper_id, claim_text |
| `evidence.jsonl` | 根拠 | claim_id, paper_id, evidence_text, locator |
| `scores.json` | スコア | features, rankings |
| `result.json` | 実行結果 | run_id, status, answer, citations |
| `eval_summary.json` | 評価結果 | gate_passed, fail_reasons, metrics |
| `warnings.jsonl` | 警告 | code, message, severity |
| `report.md` | 人間向けレポート | - |

> **Contract**: 成功/失敗に関わらず10ファイル必須。欠損はシステムエラー。
> 失敗時でも result.json, eval_summary.json, warnings.jsonl, report.md は必ず生成。


### 成功条件（強制）

```
status == "success" ⇔ gate_passed == true
```

| 条件 | 説明 |
|------|------|
| `gate_passed == true` | Verifyを通過 |
| `gate_passed == false` | status は "failed" または "needs_retry" |

> **警告**: Verify未実行のrunは success にならない

### 三位一体

| 要素 | 説明 |
|------|------|
| 静的仕様 | YAML定義が唯一の真実 |
| 動的監督 | Lyra Supervisorが品質保証 |
| 自動評価 | CI/Quality Gatesが強制 |

### 必須条件

すべての出力は:
- **再現可能** (seed固定、モデルバージョン固定)
- **根拠追跡可能** (evidence_links必須)
- **評価可能** (スコア・監査ログ)

> 「動くが説明できない」「賢そうだが再現しない」→ **不合格**

---

## 1. レイヤ構造（固定）

```
Layer 0: Human Authority
  └ 金子優（最終判断・価値定義）

Layer 1: Supervisor Layer
  └ Lyra（思考・指示・品質・乖離監査）

Layer 2: Orchestration Core
  └ JARVIS Core（契約・実行・ログ・評価）

Layer 3: Worker AIs
  ├ antigravity（設計・実装）
  ├ codex（コード生成）
  ├ LLM群（抽出・要約・評価）
  └ 外部API（PubMed, UniProt, etc）
```

---

## 2. Research Lifecycle

```mermaid
graph LR
    A[文献探索] --> B[スクリーニング]
    B --> C[抽出]
    C --> D[要約]
    D --> E[比較]
    E --> F[評価]
    F --> G[知識化]
    G --> H[仮説生成]
    H --> I[実験設計]
    I --> J[再評価]
    J --> A
```

全工程を**1 pipeline**として閉じること。

---

## 3. Stage Registry（必須）

### 仕様
- YAML記載の**全stage**が実行可能であること
- 未登録stage = **CI失敗**

### デコレータ方式

```python
@register_stage("retrieval.query_expand")
def stage_query_expand(context, artifacts):
    ...  # 最小実装（provenance必須）
```

---

## 4. Plugin仕様（統一）

### plugin.json 正式仕様

```json
{
  "id": "retrieval_st",
  "version": "1.0.0",
  "type": "retrieval|extract|summarize|score|graph|design|ops|ui",
  "entrypoint": "plugin.py:PluginClass",
  "dependencies": [],
  "hardware": {"gpu_optional": true}
}
```

> 別キーは禁止

---

## 5. Quality Gates（強制）

| Gate | 閾値 | 条件 |
|------|------|------|
| 根拠付け率 | ≥95% | 全claimにevidenceあり |
| 根拠なし事実 | =0 | factにevidenceなし禁止 |
| パイプライン完走 | =100% | 途中失敗禁止 |
| 再現性 Top10 | ≥90% | 同一入力→同一順序 |

---

## 6. CI分離

### CPU CI
- Stage Registry検証
- plugin.json検証
- Contract test
- Golden test

### ML CI
- Rerank/Embedding実行
- 再現性テスト
- 根拠率テスト

---

## 7. 禁止事項（絶対）

```yaml
# 禁止
|| true
continue-on-error: true
pass
NotImplementedError
空return
try/except握り潰し
```

---

## 8. Lyra権限

| 権限 | 説明 |
|------|------|
| 実装拒否権 | 品質不足の実装を拒否 |
| 再指示生成権 | 修正指示を生成 |
| CI失敗時介入 | 自動で診断・修正提案 |

---

## 9. 受け入れ基準（DoD）

全て満たされた時のみ「達成」:

- [ ] 全stage がregistry登録済み
- [ ] plugin.json 単一仕様
- [ ] 全stage がprovenance更新
- [ ] CI 失敗がブロック
- [ ] Golden/再現性/根拠率テスト green
- [ ] CI failure → Lyra修正指示

---

*JARVIS Research OS - MASTER_SPEC v1.0*

---

## 10. Auxiliary CLI Subcommands (Binding)

- Entry point is still `jarvis_cli.py` only.
- The following helper subcommands are allowed:
  - `papers tree`
  - `papers map3d`
  - `harvest watch`
  - `harvest work`
  - `radar run`
  - `collect papers`
  - `collect drive-sync`
  - `market propose`
- Every run from these commands must produce the required 10 bundle files via `BundleAssembler.build(...)`.
- Extra artifacts must be stored under `logs/runs/{run_id}/<feature_subdir>/`.

## 11. Result Status Vocabulary (Binding)

- `result.json.status` is restricted to:
  - `success`
  - `failed`
  - `needs_retry`
- `partial`, `budget_exceeded` and similar labels must not be used in `result.json.status`.
- Details should be recorded in `eval_summary.json.fail_reasons` and `report.md`.

### Status Decision Rule

- `gate_passed == true` -> `status = success`
- `gate_passed == false` -> `status = failed` or `needs_retry`
- `quality_report is None` -> must not be `success` (`needs_retry` with reason `VERIFY_NOT_RUN`)
