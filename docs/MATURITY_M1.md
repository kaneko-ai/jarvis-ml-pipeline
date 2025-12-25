# JARVIS Maturity M1: 構造完備（Architecture Integrity）

**バージョン**: 1.0  
**ステータス**: 実装中

---

## 目標

Registry駆動の実行、YAMLスキーマ整合、CI強制、E2Eが一本通り、ゲートが機能する状態を"仕様として固定"する。

---

## タスク一覧

| ID | タスク | 状態 |
|----|--------|------|
| M1-1 | Executor単一化（StageRegistry.get経由） | ✅ |
| M1-2 | Pipeline YAMLスキーマ固定 | ✅ |
| M1-3 | Artifacts/Provenanceスキーマ固定 | ✅ |
| M1-4 | Quality Gate最小整備 | ✅ |
| M1-5 | E2E OA10 CI完走 | ✅ |

---

## 成果物

| ファイル | 説明 |
|---------|------|
| `schemas/pipeline_v1.json` | パイプラインYAMLスキーマ |
| `schemas/artifacts_v1.json` | Artifactsスキーマ |
| `schemas/audit_v1.json` | 監査ログスキーマ |
| `.github/workflows/m1_gate.yml` | M1合格CI |

---

## DoD（Definition of Done）

### 1. 全pipelineが同一スキーマで実行できる
- **検証**: `schemas/pipeline_v1.json` に対して全YAMLを検証
- **CI**: `m1-yaml-schema` ジョブ

### 2. 未登録ステージはCIで確実に落ちる
- **検証**: 不正ステージ名で `StageNotImplementedError` 発生
- **CI**: `m1-stage-registry` ジョブ

### 3. E2E（OA10）がCIで完走し、bundle+auditが生成される
- **検証**: `e2e_oa10` パイプライン実行、claims生成確認
- **CI**: `m1-e2e-oa10` ジョブ

---

## スキーマ仕様

### Pipeline YAML（pipeline_v1.json）

```yaml
pipeline: <name>
stages:
  - id: <stage_id>  # 必須。StageRegistry登録名
    config: {}      # オプション
policies:
  seed: 42
  provenance_required: true
  fail_closed: true
```

### Artifacts（artifacts_v1.json）

```json
{
  "run_meta": {"run_id": "...", "pipeline": "...", "timestamp": "..."},
  "claims": [{"claim_id": "...", "claim_text": "...", "claim_type": "..."}],
  "evidence_links": [{"claim_id": "...", "doc_id": "...", "chunk_id": "...", "start": 0, "end": 10}],
  "quality_report": {"passed": true}
}
```

### Provenance（audit_v1.json内）

```json
{
  "doc_id": "pmid:12345",
  "chunk_id": "chunk_0",
  "start": 0,
  "end": 100,
  "source_hash": "abc123..."
}
```

---

## 計測方法

| メトリクス | 計算方法 | 閾値 |
|-----------|---------|------|
| 登録ステージ数 | `len(registry.list_stages())` | ≥ 50 |
| パイプライン適合率 | 全YAML中スキーマ適合数 | 100% |
| E2E完走率 | CI成功/試行 | 100% |
