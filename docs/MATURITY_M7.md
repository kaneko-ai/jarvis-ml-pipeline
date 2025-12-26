# JARVIS Maturity M7: Human-in-the-loop & エコシステム統合

**バージョン**: 1.0  
**ステータス**: 実装完了

---

## 目標

ツールが独立して使われるのでなく、研究者・他システムと相互にフィードバックを回せる状態にする。

---

## タスク一覧

| ID | タスク | 状態 |
|----|--------|------|
| M7-1 | Human Review Loop | ✅ |
| M7-2 | 外部ツール連携 | ✅ |
| M7-3 | Feedback Loop | ✅ |
| M7-4 | OpenAPI/Webhook | ✅ |

---

## 成果物

| ファイル | 説明 |
|---------|------|
| `jarvis_core/ops/hitl.py` | HITL（レビューキュー、フィードバック） |
| `jarvis_core/ops/integration.py` | 外部連携（Webhook、プラグインAPI） |
| `tests/test_hitl_integration.py` | M7テスト |

---

## Human Review Loop

### レビュータイプ
| タイプ | 説明 |
|-------|------|
| `claim_validation` | Claim検証 |
| `evidence_verification` | 根拠検証 |
| `rob_assessment` | バイアスリスク評価 |
| `final_approval` | 最終承認 |

### レビューステータス
- `pending` - 未処理
- `in_review` - レビュー中
- `approved` - 承認
- `rejected` - 却下
- `needs_revision` - 要修正

---

## フィードバック回収

```python
feedback = collector.collect(
    item_id="REV-001",
    reviewer="researcher1",
    rating=4,
    accuracy_score=0.9,
    comments="Good extraction"
)
```

### 統計
```python
stats = collector.get_statistics()
# {"total": 100, "avg_rating": 4.2, "avg_accuracy": 0.87}
```

---

## Webhook通知

### イベントタイプ
| イベント | 説明 |
|---------|------|
| `run.started` | ラン開始 |
| `run.completed` | ラン完了 |
| `run.failed` | ラン失敗 |
| `quality.alert` | 品質アラート |
| `drift.detected` | 劣化検知 |
| `review.required` | レビュー要求 |

---

## プラグインAPI

```python
registry.register("POST", "/api/claims", handler, "Submit claims")
spec = registry.get_openapi_spec()  # OpenAPI 3.0形式
```

---

## DoD（Definition of Done）

- [x] Claimのレビューキュー・承認フロー
- [x] フィードバック回収とモデル改善ループ
- [x] 外部ツール（Zotero/Notion等）との連携可能
- [x] Webhook/OpenAPI仕様の公開
