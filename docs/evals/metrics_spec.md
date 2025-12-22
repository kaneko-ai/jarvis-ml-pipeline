"""Metrics Spec.

Per RP-135, defines evaluation metrics precisely.
"""
# Evaluation Metrics Specification

## claim_precision

**Definition:**
Ratio of claims that are fully supported by cited evidence.

**Formula:**
```
claim_precision = supported_claims / total_claims
```

**Criteria for "supported":**
1. Claim must have at least 1 citation
2. Citation must have valid Locator (page/span/sentence_id)
3. Section of evidence must be appropriate (not References/Methods unless claim is about methodology)
4. Evidence text must semantically support the claim (not contradict)

---

## citation_precision

**Definition:**
Ratio of citations that correctly support their associated claims.

**Formula:**
```
citation_precision = valid_citations / total_citations
```

**Criteria for "valid":**
1. Locator is complete (source_id + at least one of: page, span, sentence_id)
2. Section is appropriate for the claim type
3. Evidence text snippet aligns with claim semantics

---

## entity_hit_rate

**Definition:**
Ratio of expected entities that appear in the output.

**Formula:**
```
entity_hit_rate = found_entities / expected_entities
```

**Note:**
Expected entities are defined in the frozen evaluation set.

---

## success_rate

**Definition:**
Ratio of runs that complete with status=success or status=partial.

**Statuses:**
- `success`: All quality gates passed
- `partial`: Some gates passed, usable output generated
- `failed`: Fatal error, no usable output

**Formula:**
```
success_rate = (success_count + partial_count) / total_runs
```

---

## evidence_density

**Definition:**
Average number of evidence citations per claim.

**Formula:**
```
evidence_density = total_citations / total_claims
```

**Target:** >= 1.5 citations per claim
