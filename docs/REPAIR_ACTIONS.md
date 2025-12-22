# Repair Actions Documentation

Per RP-185, this documents the available remediation actions.

## Overview

Remediation actions are deterministic, minimal-side-effect operations that modify run configuration to recover from failures.

---

## Actions

### SWITCH_FETCH_ADAPTER

**Intent:** Switch to next fetch adapter when PDF fetch fails.

**Order:** Local → PMC → Unpaywall → HTML fallback

**Safety:** ✅ Safe. Only changes fetch source, no PII exposure.

**When Applied:**
- FETCH_PDF_FAILED
- EXTRACT_PDF_FAILED

---

### INCREASE_TOP_K

**Intent:** Retrieve more candidates to improve coverage.

**Changes:** `top_k` += 5 (max 50)

**Safety:** ✅ Safe. May increase latency but no data exposure.

**When Applied:**
- CITATION_GATE_FAILED
- ENTITY_MISS
- As fallback for fetch failures

---

### TIGHTEN_MMR

**Intent:** Reduce redundant chunks to improve precision.

**Changes:** `mmr_lambda` += 0.1 (max 0.9)

**Safety:** ✅ Safe. Reduces noise, may reduce coverage.

**When Applied:**
- LOW_CLAIM_PRECISION
- CITATION_GATE_FAILED (secondary)

---

### CITATION_FIRST_PROMPT

**Intent:** Switch to citation-prioritizing prompt strategy.

**Changes:** `prompt_strategy` = "citation_first"

**Safety:** ✅ Safe. Changes generation behavior only.

**When Applied:**
- CITATION_GATE_FAILED (after INCREASE_TOP_K)

---

### BUDGET_REBALANCE

**Intent:** Rebalance budget to prioritize retrieval.

**Changes:**
- `max_generation_tokens` halved
- `budget_priority` = "retrieval"

**Safety:** ✅ Safe. May produce shorter output.

**When Applied:**
- BUDGET_EXCEEDED

---

### MODEL_ROUTER_SAFE_SWITCH

**Intent:** Switch to lighter/safer model on model errors.

**Changes:** `model_provider` to fallback

**Fallback Order:** gemini → ollama → rule

**Safety:** ✅ Safe. May reduce quality.

**When Applied:**
- MODEL_ERROR
- JUDGE_TIMEOUT

---

## Determinism Guarantee

All actions guarantee:
- Same input → Same output
- No random behavior (respects seed)
- No PII/secrets in output

## Adding Custom Actions

```python
from jarvis_core.runtime.remediation import RemediationAction, ActionResult

class MyAction(RemediationAction):
    action_id = "MY_ACTION"
    description = "My custom action"

    def apply(self, config, state):
        return ActionResult(
            success=True,
            config_changes={"my_param": "new_value"},
            message="Applied my action",
        )
```
