> Authority: GATE (Level 3, Binding)

# JARVIS SLA Tiers

商用/公開向けSLA定義。

---

## SLA-Tier 0 (Internal/Research)

| 項目 | 値 |
|------|-----|
| Availability | best-effort |
| P95 Latency | 制限なし |
| Completion | 保証なし |
| Retry | 無制限（Kill条件内） |
| Rate Limit | 1000 req/min, 10000 runs/day |

**用途**: 内部開発、研究、テスト

---

## SLA-Tier 1 (Public/Free)

| 項目 | 値 |
|------|-----|
| Availability | 99.0% |
| P95 Latency | ≤ 30秒（run受付まで） |
| Completion | run_id発行保証のみ |
| Retry | 1回 |
| Rate Limit | 5 req/min, 20 runs/day |

**用途**: 公開API、無料ユーザー

---

## SLA-Tier 2 (Commercial)

| 項目 | 値 |
|------|-----|
| Availability | 99.9% |
| P95 Latency | ≤ 5秒（run受付まで） |
| Completion | run_id + status更新保証 |
| Retry | 5回 |
| Rate Limit | 60 req/min, 1000 runs/day |

**用途**: 商用API、有料ユーザー

---

## SLA違反時の挙動

SLA違反は例外ではなく**状態**として扱う。

```json
{
  "status": "degraded",
  "sla_tier": "public",
  "violation": {
    "reason": "Latency exceeded SLA",
    "latency_ms": 35000
  }
}
```

### 対応

1. `run.status = degraded or failed`
2. `events.jsonl` に `SLA_VIOLATION` 記録
3. 利用者へ事前定義メッセージ返却

### 禁止

- 再試行による隠蔽
- 無言失敗

---

## Abuse検知

以下はAbuseとみなす:

| 条件 | アクション |
|------|----------|
| 同一入力の高速連続実行（10秒内に3回以上） | blocked |
| failed runの異常連打（同一入力で5回以上） | blocked |
| 巨大入力連続送信 | blocked |

---

*JARVIS SLA Tiers v1.0*
