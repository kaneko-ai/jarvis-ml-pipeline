# JARVIS Critical Enforcement Layer
# 導入指示書 v1.0

> **第2位強制文書**: MASTER_SPECに次ぐ

---

## 1. Stage Registry

### 目的
- YAML記載の**全stage**が実装済みであること
- 未登録 = **CI失敗**

### 実装

```
jarvis_core/pipelines/stage_registry.py
```

```python
@register_stage("stage.name")
def stage_handler(context, artifacts):
    # 1. artifacts更新
    # 2. provenance追加
    # 3. ログ出力
    return artifacts
```

---

## 2. Plugin統一仕様

### 正式 plugin.json

```json
{
  "id": "plugin_id",
  "version": "1.0.0",
  "type": "retrieval|extract|summarize|score|graph|design|ops|ui",
  "entrypoint": "plugin.py:PluginClass",
  "dependencies": [],
  "hardware": {"gpu_optional": true}
}
```

### 禁止キー
- `name`→`id`に統一
- `requires`→`dependencies`に統一

---

## 3. 最小実装義務

### 禁止

```python
pass
NotImplementedError
return  # 空
```

### 必須

```python
def stage_x(context, artifacts):
    # 1. artifacts更新
    artifacts.metadata["x"] = "value"
    
    # 2. provenance追加
    artifacts.add_claim(Claim(
        claim_id="c-xxx",
        claim_text="Stage completed",
        evidence=[EvidenceLink(...)]
    ))
    
    # 3. ログ
    log_audit("stage_x", "completed")
    
    return artifacts
```

---

## 4. CI強制

### 禁止

```yaml
# 絶対禁止
|| true
continue-on-error: true
```

### 分離

| CI | 内容 |
|----|------|
| CPU | Registry検証、plugin.json、contract test |
| ML | 埋め込み、再現性、根拠率 |

---

## 5. テスト

| テスト | 内容 |
|--------|------|
| Golden | 同一入力→同一出力 |
| 再現性 | Top10一致率≥90% |
| 根拠率 | ≥95% |

---

## 6. Lyra連動

### 発火条件
- CI failure
- Golden差分
- Provenance違反

### 出力

```json
{
  "issue": "Unregistered stage",
  "severity": "blocker",
  "recommended_action": "Implement stage",
  "confidence": 0.93
}
```

---

## 7. 受け入れ基準

- [x] 全stageがregistry登録
- [x] plugin.json統一仕様
- [x] 全stageがprovenance更新
- [x] CI失敗がブロック
- [x] Golden/再現性/根拠率テスト
- [x] Lyra修正指示連動

---

*CRITICAL_ENFORCEMENT_LAYER v1.0*
