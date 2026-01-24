# Release Notes v4.3

> Authority: REFERENCE (Level 2, Non-binding)


## Overview

JARVIS Research OS v4.3 implements comprehensive test infrastructure hardening and foundational features for reproducible research workflows.

---

## Breaking Changes

> [!WARNING]
> The following changes may require updates to existing code:

### BudgetManager API Change
- **Old**: `BudgetManager(Budget(max_tokens=1000))`
- **New**: `BudgetManager(BudgetLimits(max_tokens=1000))`
- **Migration**: Replace `Budget` with `BudgetLimits`, use `add_tokens()` instead of `use_tokens()`

### Runtime Module Exports
- Removed: `RetryPolicy`, `with_retry` from `jarvis_core.runtime`
- Use `jarvis_core.runtime.retry` module directly

---

## New Features

### Test Infrastructure
- **Core/Legacy Markers**: Tests separated into blocking `@pytest.mark.core` and non-blocking `@pytest.mark.legacy`
- **Network Guard**: Automatic network blocking for core tests
- **Deterministic Time/Seed**: `freeze_time()`, `enforce_seed()` for reproducibility

### Retrieval & Extraction
- **PDF Engine Chain**: Automatic fallback (PyMuPDF → pdfminer → PyPDF2)
- **HTML Fallback**: Extract abstracts when PDFs unavailable
- **Sectionizer**: IMRaD section detection
- **Hybrid Retrieval**: Combined BM25 + vector scoring

### Knowledge Graph
- **Entity Normalizer**: Immunology synonym expansion
- **2-Hop Retrieval**: Subgraph context for generation

### Evaluation
- **Claim Classifier**: Rule-based fact/interpretation detection
- **Noise Injection**: Robustness testing
- **Drift Detection**: Entity distribution monitoring

### Runtime
- **Budget Manager**: All-layer budget enforcement
- **Durable Checkpoints**: Resume long-running tasks
- **Status Definitions**: Fixed success/partial/fail semantics

### Web API
- **FastAPI Integration**: `/run`, `/show-run/{id}`, `/runs` endpoints
- **Token Authentication**: `JARVIS_WEB_TOKEN` environment variable

### Observability
- **TraceContext**: Mandatory trace propagation
- **Run Summarizer**: Human-readable run summaries
- **KPI Reporter**: Success rate tracking

---

## Migration Guide

### 1. Update BudgetManager Usage

```python
# Before
from jarvis_core.runtime import Budget, BudgetManager
manager = BudgetManager(Budget(max_tokens=1000))

# After
from jarvis_core.runtime import BudgetLimits, BudgetManager
manager = BudgetManager(BudgetLimits(max_tokens=1000))
```

### 2. Mark Tests

```python
# Add to core test files
import pytest
pytestmark = pytest.mark.core
```

### 3. Install Dependencies

```bash
pip install -r requirements.lock
```

---

## Known Issues

- Telemetry contract v2 tests marked as legacy due to API differences
- Web UI (RP-169/170) not yet implemented

---

## Contributors

- Research OS Team
