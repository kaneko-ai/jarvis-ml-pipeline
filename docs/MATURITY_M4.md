# JARVIS Maturity M4: 運用完備（Ops-ready Research OS）

> Authority: REFERENCE (Level 2, Non-binding)


**バージョン**: 1.0  
**ステータス**: 実装完了

---

## 目標

現実運用（失敗・欠損・レート制限・長時間）に耐える。
"止まるべき時に止まり、続ける時はdegradedとして続ける"が明確。

---

## タスク一覧

| ID | タスク | 状態 |
|----|--------|------|
| M4-1 | レート制限・バックオフ・キュー | ✅ |
| M4-2 | ジョブ再開（Resume） | ✅ |
| M4-3 | 観測性（Observability） | ✅ |
| M4-4 | Runbook（運用手順） | ✅ |

---

## 成果物

| ファイル | 説明 |
|---------|------|
| `jarvis_core/ops/rate_limiter.py` | レート制限・リトライ |
| `jarvis_core/ops/checkpoint.py` | チェックポイント・再開 |
| `jarvis_core/ops/metrics.py` | メトリクス・観測性 |
| `docs/RUNBOOK.md` | 運用手順書 |
| `tests/test_ops.py` | Opsテスト |

---

## レート制限

### PubMed/PMC
| 条件 | 制限 |
|-----|------|
| API keyなし | 3 req/s |
| API keyあり | 10 req/s |

### リトライ戦略
```python
config = RateLimitConfig(
    max_retries=3,
    base_delay_sec=1.0,
    max_delay_sec=60.0,
    exponential_base=2.0,
    jitter=True
)
```

---

## チェックポイント

### 保存場所
```
artifacts/<run_id>/checkpoint.json
```

### 再開コマンド
```bash
python -m jarvis_core.cli run --resume --run-id <run_id>
```

### ステージ状態
- `pending` - 未開始
- `running` - 実行中
- `completed` - 完了
- `failed` - 失敗
- `degraded` - 劣化状態で完了

---

## 観測性

### Run Metrics
| メトリクス | 説明 |
|-----------|------|
| `total_duration_ms` | 総実行時間 |
| `api_calls` | API呼び出し回数 |
| `api_errors` | APIエラー回数 |
| `failed_stages` | 失敗ステージ |
| `degraded_stages` | 劣化ステージ |

### Quality Metrics
| メトリクス | 説明 |
|-----------|------|
| `provenance_rate` | 根拠率 |
| `pico_consistency_rate` | PICO整合率 |
| `gates_passed` | 通過ゲート数 |

### 蓄積
```
artifacts/metrics_aggregate.jsonl
```

---

## DoD（Definition of Done）

- [x] 途中失敗から再開できる
- [x] 観測メトリクスが継続的に蓄積できる
- [x] 運用手順が文書化され、属人化避ける
