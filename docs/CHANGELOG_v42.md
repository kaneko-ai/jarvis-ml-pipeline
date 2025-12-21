# CHANGELOG v4.2

## Sprint 2: 運用域（Infrastructure）

### 道G: Task Graph & Parallel Execution
- **runtime/task_graph.py**: DAG-based task execution with dependency resolution
  - Parallel/sequential execution modes
  - Cache-aware task skipping
  - Span tracking per task node
  - **Guarantee**: 並列度変更でも結果同一（再現性）

### 道F: Streaming Bundle & Checkpoint
- **runtime/streaming_bundle.py**: Atomic incremental bundle writing
  - Checkpoint/resume for crash recovery
  - **Guarantee**: 強制終了してもbundleが残り再開可能

### 道E: Incremental Indexing
- **index/pipeline.py**: Staged indexing (ingest→normalize→chunk→index)
- **index/incremental_state.py**: Hash-based state management
- **index/dedup.py**: Exact + near-duplicate detection
  - **Guarantee**: 同一コーパス2回目は大半スキップ

### 道H: Multi-Level Cache
- **cache/multi_level.py**: L1 memory + L2 disk cache
- **cache/key_contract.py**: Deterministic cache key computation
  - Key includes: input_hash, extractor_version, model_version, thresholds, config_hash
  - **Guarantee**: 取り違えゼロ

### 道K: Robustness & Recovery
- **runtime/circuit_breaker.py**: Circuit breaker with exponential backoff
  - Failure classification: INPUT/CONFIG/MODEL/NETWORK/TIMEOUT/BUDGET
  - Partial result preservation
  - **Guarantee**: 外部障害でも部分成果が残る

### 道M(min): Performance Report
- **perf/report.py**: Fixed-schema performance report
  - Span/SLO/Budget/Cache statistics in JSON

---

## Sprint 3: 最強化（Optimization）

### 道I: Hybrid Retrieval v2
- **retrieval/hybrid_router.py**: Query-aware routing (BM25/Dense/Hybrid)
  - Budget-aware routing decisions
- **retrieval/two_stage.py**: Cheap candidates + expensive rerank
  - Budget threshold for rerank skipping
- **retrieval/graph_boost.py**: Citation/neighbor graph boosting
  - Bridge paper discovery

### 道J: Cost-Quality Planning
- **cost_planner/cost_model.py**: Cost estimation from span measurements
- **cost_planner/quality_gain.py**: Quality estimation for planning
- **cost_planner/pareto.py**: Pareto-optimal selection
  - **Guarantee**: SLO/Budget下で品質最大化

### 道L: Security & Privacy
- **security/pii_scan.py**: PII detection (email, phone, SSN, etc.)
- **security/redaction.py**: Format-preserving redaction
- **security/storage_policy.py**: Storage rule enforcement
  - **Guarantee**: 機微情報が成果物に残らない

### 道M(full): Dashboard & Scorecard
- **perf/dashboard.py**: Full dashboard with fixed schema
  - Top slow stages, cost breakdown, cache stats, quality metrics
- **Scorecard**: Quality gates (unsupported rate, regression, SLO)

---

## Test Results

```
502 passed in 5.26s
```

## Fixed Schema Contracts

| Component | Schema Location |
|-----------|-----------------|
| PerfReport | `perf/report.py` → `schema_version: 1.0` |
| Dashboard | `perf/dashboard.py` → `schema_version: 1.0` |
| CacheKey | `cache/key_contract.py` → deterministic |
| Checkpoint | `runtime/streaming_bundle.py` |
| FailureReason | `runtime/circuit_breaker.py` → enum |

## Backward Compatibility

- bundle_layout: preserved
- trace: extended (not broken)
- errors: extended (not broken)
- audit_view_contract: preserved
