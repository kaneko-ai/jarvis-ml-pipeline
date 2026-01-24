# JARVIS Maturity M3: メタ分析完備（Meta-analysis Core Rigor）

> Authority: REFERENCE (Level 2, Non-binding)


**バージョン**: 1.0  
**ステータス**: 実装完了

---

## 目標

"文章としてもっともらしい"ではなく、統計メタ分析として破綻避ける抽出・評価・統合設計を成立させる。

---

## タスク一覧

| ID | タスク | 状態 |
|----|--------|------|
| M3-1 | PICO整合ゲート | ✅ |
| M3-2 | 効果量抽出の型安全 | ✅ |
| M3-3 | ROB準拠 | ✅ |
| M3-4 | 異質性構造化 | ✅ |
| M3-5 | PRISMAログ | ✅ |

---

## 成果物

| ファイル | 説明 |
|---------|------|
| `schemas/meta_extract_v1.json` | メタ分析抽出スキーマ |
| `schemas/rob_v1.json` | バイアスリスク評価スキーマ |
| `jarvis_core/evaluation/pico_consistency.py` | PICO整合性チェッカー |
| `tests/test_meta_typed_extraction.py` | メタ分析テスト（15件） |

---

## PICO整合ゲート

### チェック項目
| 要素 | 検証内容 |
|-----|---------|
| Population | 対象集団のキーワード一致 |
| Intervention | 介入/曝露の一致 |
| Comparator | 比較対象の一致 |
| Outcome | アウトカムの一致 |
| Direction | 効果方向（beneficial/harmful）の一致 |

### 整合性レベル
```python
class ConsistencyLevel(Enum):
    CONSISTENT = "consistent"      # 一致
    PARTIAL = "partial"            # 部分一致
    INCONSISTENT = "inconsistent"  # 不一致
    UNKNOWN = "unknown"            # 判定不能
```

---

## 効果量の型安全

### サポートする効果量タイプ
| コード | 説明 |
|-------|------|
| OR | Odds Ratio |
| RR | Risk Ratio |
| HR | Hazard Ratio |
| RD | Risk Difference |
| MD | Mean Difference |
| SMD | Standardized Mean Difference |
| WMD | Weighted Mean Difference |

### 必要フィールド
```json
{
  "measure": "OR",
  "value": 0.75,
  "ci_lower": 0.60,
  "ci_upper": 0.93,
  "direction": "beneficial",
  "provenance": {"doc_id": "...", "start": 0, "end": 100}
}
```

---

## ROB評価スキーマ

### RoB2ドメイン（RCT用）
1. ランダム化プロセス
2. 意図した介入からの逸脱
3. 欠測データ
4. アウトカム測定
5. 選択的報告

### 判定
- `low`: 低リスク
- `some_concerns`: 一部懸念
- `high`: 高リスク

### 根拠span必要
```json
{
  "domain_name": "randomization",
  "judgement": "low",
  "provenance": [{"doc_id": "...", "start": 100, "end": 200}]
}
```

---

## DoD（Definition of Done）

- [x] 一次研究セットからPICO・効果量・ROBが根拠付きで抽出できる
- [x] 不整合（PICOズレ/方向ズレ/数値ズレ）がゲートで落ちる
- [x] 根拠なしのROB評価は非推奨（スキーマで強制）
