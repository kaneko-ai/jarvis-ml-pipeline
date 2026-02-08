# Migration Guide

Target migration: `v5.x -> v1.0.0`

JARVIS Research OS スキーマ・API変更時の移行手順

---

## Phase 2-ΩΩ への移行

### 破壊的変更

#### 1. Report生成にEvidence ID必須化

**変更内容**: report.mdのすべての結論にEvidence IDが必須

**影響範囲**:
- `jarvis_core/stages/generate_report.py`
- `jarvis_core/report/generator.py`

**移行手順**:
1. 既存のreport生成ロジックを新しい`generate_report.py`に置換
2. `claims.jsonl`と`evidence.jsonl`が存在することを確認
3. Support level判定が正しく動作することをテスト

**後方互換性**: なし（Evidence IDなしのreportは生成不可）

---

#### 2. uv + lock による依存管理

**変更内容**: `pip install`から`uv sync --frozen`へ移行

**影響範囲**:
- ローカル開発環境
- CI/CD (GitHub Actions)

**移行手順**:

```bash
# 1. uvインストール
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 既存venv削除
rm -rf .venv

# 3. uv syncで再構築
uv sync --dev

# 4. 動作確認
uv run python -c "import jarvis_core; print('OK')"
```

**後方互換性**: `pip install`は非推奨（動作するが警告）

---

#### 3. Quality Gates厳格化

**変更内容**: support_rate >= 0.90 が必須

**影響範囲**:
- パイプライン実行結果
- CI/CD

**移行手順**:
1. 既存パイプラインで`eval_summary.json`の`support_rate`を確認
2. < 0.90の場合は以下を実施:
   - Evidence収集を強化
   - または`推測`扱いに降格

**後方互換性**: なし（< 0.90はfail）

---

### スキーマ変更

#### cost_report.json (NEW)

```json
{
  "stages": [
    {
      "stage_name": "extraction.claims",
      "duration_ms": 1500,
      "api_calls": 3,
      "prompt_tokens": 1000,
      "completion_tokens": 500
    }
  ],
  "totals": {
    "total_duration_ms": 15000,
    "total_tokens": 30000
  }
}
```

**移行**: 既存bundleには存在しない → 新規run必要

---

#### report.md (CHANGED)

**旧形式**:
```markdown
- CD73 is highly expressed in tumors
```

**新形式**:
```markdown
- 結論: CD73 is highly expressed in tumors
  Claim: claim_001
  Evidence: [ev_001, ev_002]
  Support: Strong
  Uncertainty: 確定
  Notes: —
```

**移行**: 既存reportは手作業で更新、または再生成

---

### 設定ファイル変更

#### policies/inference_policy.yaml (EXTENDED)

```yaml
budget:
  budget_tokens_per_run: 50000  # 既存

degradation:  # NEW
  on_budget_exceeded: degrade  # fail | degrade
  degrade_actions:
    - reduce_top_k: 5
    - disable_counter_evidence: true
```

**移行**: 既存policyファイルに`degradation`セクション追加

---

## ロールバック手順

Phase 2-ΩΩからPhase 2 Coreに戻す場合:

```bash
# 1. 特定コミットにリセット
git checkout <Phase2-Core-commit>

# 2. 依存関係再構築
uv sync --dev

# 3. 旧スキーマで動作確認
uv run pytest tests/ -v
```

**注意**: Phase 2-ΩΩで生成したbundleは互換性なし

---

## 互換性マトリクス

| Component | Phase 1 | Phase 2 Core | Phase 2-ΩΩ |
|-----------|---------|--------------|------------|
| 10-file bundle | ✅ | ✅ | ✅ |
| claims.jsonl | ❌ | ✅ | ✅ |
| evidence.jsonl | ❌ | ✅ | ✅ |
| cost_report.json | ❌ | ❌ | ✅ |
| Evidence ID in report | ❌ | ❌ | ✅ (必須) |
| uv + lock | ❌ | ❌ | ✅ (推奨) |

---

## トラブルシューティング

### uv sync失敗

```bash
# lockファイル再生成
uv lock --upgrade
uv sync --dev
```

### Evidence ID欠損エラー

```
UNSUPPORTED_CLAIM: claim_001 has no evidence
```

**対処**: `evidence.jsonl`で該当claim_idのevidenceを確認、存在しない場合は結論を`推測`に降格

### 予算超過でfail

```bash
# fast profileで再実行
uv run python jarvis_cli.py run --goal "query" --profile fast
```

---

## 問い合わせ

移行で問題が発生した場合:
1. `RUNBOOK.md`の該当セクションを確認
2. GitHub Issuesで報告
