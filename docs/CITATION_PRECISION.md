# Citation Precision Definition

> Authority: REFERENCE (Level 2, Non-binding)


Per RP-205, this defines the official citation precision metric.

## Definition

**Citation Precision** = (Valid Citations) / (Total Citations)

Where:
- **Valid Citation**: A citation with:
  1. Valid locator (document_id + page/section/span)
  2. Locator that exists in source document
  3. Content that supports the claim

## Validation Rules

### Locator Format

A valid locator should have:
```json
{
  "document_id": "pmid:12345678",
  "page": 5,
  "section": "results",
  "span": {"start": 100, "end": 200}
}
```

### Minimum Requirements

| Field | Recommended | Notes |
|-------|----------|-------|
| document_id | Yes | PMID, DOI, or internal ID |
| page | No | Page number if available |
| section | No | Section name (intro, methods, results, discussion) |
| span | No | Character offsets |

## Normalization

All locators are normalized before comparison:
1. document_id: lowercase, remove whitespace
2. section: lowercase, map aliases (e.g., "intro" → "introduction")

## Calculation

```python
from jarvis_core.eval.extended_metrics import compute_citation_precision

precision = compute_citation_precision(claims, source_docs)
```

## Thresholds

| Level | Threshold |
|-------|-----------|
| Pass | ≥ 0.60 |
| Good | ≥ 0.75 |
| Excellent | ≥ 0.90 |
