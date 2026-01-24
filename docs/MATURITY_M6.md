# JARVIS Maturity M6: 長期信頼性・セキュリティ・コンプライアンス

> Authority: REFERENCE (Level 2, Non-binding)


**バージョン**: 1.0  
**ステータス**: 実装完了

---

## 目標

長期稼働・チーム運用・規制対応に耐える堅牢な基盤を構築する。

---

## タスク一覧

| ID | タスク | 状態 |
|----|--------|------|
| M6-1 | モデル劣化検知 | ✅ |
| M6-2 | アクセス制御（RBAC） | ✅ |
| M6-3 | GDPR対応 | ✅ |
| M6-4 | 監査ログ | ✅ |

---

## 成果物

| ファイル | 説明 |
|---------|------|
| `jarvis_core/ops/drift_detector.py` | 劣化検知・Goldenテスト |
| `jarvis_core/ops/security.py` | アクセス制御・GDPR |
| `tests/test_reliability_security.py` | M6テスト |

---

## モデル劣化検知

### Goldenテスト
```python
test_case = GoldenTestCase(
    test_id="golden_1",
    input_data={"query": "..."},
    expected_output={"score": 0.95},
    tolerance=0.05,
    critical=True
)
```

### アラート重要度
| 劣化率 | 重要度 |
|-------|--------|
| > 30% | critical |
| > 20% | high |
| > 15% | medium |
| > 10% | low |

---

## アクセス制御（RBAC）

### ロール
| ロール | パーミッション |
|-------|---------------|
| `admin` | read, write, execute, delete, admin |
| `researcher` | read, write, execute |
| `reviewer` | read, execute |
| `readonly` | read |

### 監査ログ
- 全アクセスを`audit/access_log.jsonl`に記録
- タイムスタンプ、ユーザー、アクション、リソース、許可/拒否

---

## GDPR対応

### PII検出
- 人名、電話番号、メールアドレス

### 匿名化
```python
anonymized = gdpr.anonymize_text(text)
# "user@test.com" → "[EMAIL_REDACTED]"
```

### 削除リクエスト
```python
request = gdpr.create_deletion_request(
    requester="user1",
    target_type="document",
    target_id="doc123",
    reason="GDPR Article 17"
)
```

---

## DoD（Definition of Done）

- [x] Goldenテスト回帰検知がCIに組み込み可能
- [x] 品質スコアの有意な劣化でアラートが自動発報される
- [x] RBACとfact-levelアクセス制御
- [x] GDPR削除リクエスト処理可能
