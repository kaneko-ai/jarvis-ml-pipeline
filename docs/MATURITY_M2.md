# JARVIS Maturity M2: 再現性完備（Reproducibility & Snapshot）

**バージョン**: 1.0  
**ステータス**: 実装完了

---

## 目標

外部依存（PubMed/PMC/モデル）を含んでも、再実行で同等の結果に戻れる状態を作る。
「再現性90%」を"根拠ある数値"にする。

---

## タスク一覧

| ID | タスク | 状態 |
|----|--------|------|
| M2-1 | Snapshot戦略 | ✅ |
| M2-2 | Run Determinism Policy | ✅ |
| M2-3 | Fail-Closed / Fail-Open ポリシー | ✅ |
| M2-4 | 再現性テスト三層化 | ✅ |

---

## 成果物

| ファイル | 説明 |
|---------|------|
| `configs/policies/reproducibility.yml` | 再現性ポリシー |
| `schemas/snapshot_v1.json` | Snapshotスキーマ |
| `jarvis_core/ops/snapshot.py` | Snapshotモジュール |
| `tests/test_reproducibility_snapshot.py` | 再現性テスト |

---

## Snapshot戦略

### 保存対象
| 項目 | 説明 |
|-----|------|
| `query_package` | 検索クエリ・フィルタ・ソース |
| `search_results` | PMIDリスト・順位・スコア |
| `retrieved_content` | 取得本文（content_hash付き） |
| `chunk_mapping` | chunk_id ↔ span対応 |
| `model_io` | prompt_hash/model_id/params |

### 再実行時の挙動
```yaml
replay:
  prefer_snapshot: true      # スナップショット優先
  fallback_to_live: false    # ライブ取得フォールバック禁止
```

---

## Fail Policy

| モード | 動作 |
|-------|------|
| **Fail-Closed**（デフォルト） | API失敗→即中断、成功扱い禁止 |
| **Fail-Open** | 継続可能、ただし`degraded`フラグ必須 |

```yaml
fail_policy:
  default: "closed"
  open:
    degraded_flag_required: true
    max_degraded_ratio: 0.2  # 20%超でパイプライン失敗
```

---

## 再現性メトリクス

| メトリクス | 定義 | 閾値 |
|-----------|------|------|
| Top10一致率 | 同一クエリで上位10件一致 | ≥ 90% |
| TopK Jaccard | 上位K件の集合類似度 | ≥ 0.8 |
| スコア差異 | 同一文書のスコア差 | ≤ 0.05 |

---

## DoD（Definition of Done）

- [x] 同一入力の再実行でTopK一致が閾値を満たす
- [x] ズレ原因がauditで判別可能（データ更新/モデル更新/取得失敗）
- [x] degraded runが"成功"として集計されない
