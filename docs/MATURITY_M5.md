# JARVIS Maturity M5: 科学的妥当性完備（Scientific Validity）

**バージョン**: 1.0  
**ステータス**: 実装完了

---

## 目標

「Aに一致＝正解」という誤学習を防ぎ、反証・欠落・論争を扱える。

---

## タスク一覧

| ID | タスク | 状態 |
|----|--------|------|
| M5-1 | 反証探索（Counterevidence Search） | ✅ |
| M5-2 | 論争マップの強制 | ✅ |
| M5-3 | データセットガバナンス | ✅ |
| M5-4 | 校正（Calibration） | ✅ |

---

## 成果物

| ファイル | 説明 |
|---------|------|
| `jarvis_core/evaluation/counterevidence.py` | 反証探索・論争マップ |
| `jarvis_core/evaluation/dataset_governance.py` | データガバナンス |
| `schemas/controversy_v1.json` | 論争マップスキーマ |
| `tests/test_scientific_validity.py` | 科学的妥当性テスト |

---

## 反証探索

### スタンス分類
| スタンス | 説明 |
|---------|------|
| `supporting` | 主張を支持 |
| `opposing` | 主張に反対 |
| `neutral` | 中立 |
| `inconclusive` | 判断不能 |

### 論争レベル
| レベル | 条件 |
|-------|------|
| `none` | 反対なし |
| `low` | 反対 < 10% |
| `moderate` | 10% ≤ 反対 < 30% |
| `high` | 30% ≤ 反対 < 50% |
| `unresolved` | 反対 ≥ 50% |

---

## 論争マップ

### 必須出力
```json
{
  "topic": "...",
  "supporting_arguments": [{"text": "...", "provenance": {...}}],
  "opposing_arguments": [{"text": "...", "provenance": {...}}],
  "undecided_points": ["..."],
  "controversy_level": "moderate"
}
```

### 一方的結論チェック
- 高論争のトピックがmain_conclusionにある場合は警告

---

## データセットガバナンス

### マニフェスト
- バージョン管理
- 除外理由の記録
- 品質スコア閾値

### 除外リスト
- ノイズ教師の除外
- 破棄ログ（exclusions.jsonl）

---

## DoD（Definition of Done）

- [x] 反証探索がパイプラインに組み込まれる
- [x] 論争がある領域で一方的結論を出さない
- [x] 学習データが版管理され、悪いデータが混入しにくい
