# Audit View Contract

Per V4-D03, this document defines the standard structure for `audit.md` output.

## Required Sections (in order)

### 1. Header
```markdown
# Audit Report
**Run ID**: {run_id}
**Timestamp**: {timestamp}
**Workflow**: {workflow_name}
```

### 2. Summary Metrics
```markdown
## Summary
| Metric | Value |
|--------|-------|
| Total Claims | {n} |
| Facts with Evidence | {n} |
| Unsupported Claims | {n} |
| Inferences | {n} |
| Unsupported Rate | {%} |
```

### 3. Quality Gate Status
```markdown
## Quality Gate
**Status**: ✅ PASSED / ❌ FAILED

### Gate Conditions
- [ ] Unsupported FACT rate ≤ 10%
- [ ] All FACTs have EvidenceRef
- [ ] No contradictions detected
```

### 4. High-Risk Items
```markdown
## High-Risk Items
Items requiring human review, sorted by risk score.

### 🔴 High Risk
- {item_id}: {reason}

### 🟡 Medium Risk
- {item_id}: {reason}
```

### 5. Provenance Summary
```markdown
## Provenance
- **Sources**: {n} documents
- **Chunks**: {n} extracted
- **Model**: {model_name}
- **Thresholds**: relevance={x}, alignment={y}
```

### 6. Flags and Warnings
```markdown
## Flags
- ⚠ {flag_description}
```

## Granularity
- Each claim/fact should be individually addressable by ID
- Evidence should link to source locator (page, paragraph)
- Risk scores should be explicit (0-1 scale)

## Order
Sections must appear in the order specified above.
