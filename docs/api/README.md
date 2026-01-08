# JARVIS Research OS API Reference

## Overview

JARVIS Research OS provides both a Python API for programmatic access and a REST API for web integration.

## Python API

### Evidence Grading

```python
from jarvis_core.evidence import grade_evidence, EvidenceLevel

grade = grade_evidence(
    title="A randomized controlled trial of...",
    abstract="Methods: We conducted a double-blind RCT...",
    use_llm=False,
)

print(f"Level: {grade.level.value}")  # "1b"
print(f"Type: {grade.study_type.value}")  # "randomized_controlled_trial"
print(f"Confidence: {grade.confidence}")  # 0.85
```

### Citation Analysis

```python
from jarvis_core.citation import (
    extract_citation_contexts,
    classify_citation_stance,
    CitationGraph,
)

# Extract citations from text
contexts = extract_citation_contexts(
    text="Previous work [1] showed significant results...",
    paper_id="current_paper",
    reference_map={"1": "cited_paper_id"},
)

# Classify stance
for ctx in contexts:
    stance = classify_citation_stance(ctx.get_full_context())
    print(f"Stance: {stance.stance.value}")  # "support", "contrast", "mention"

# Build citation graph
graph = CitationGraph()
graph.add_edge("paper_a", "paper_b", stance=CitationStance.SUPPORT)
supporting = graph.get_supporting_citations("paper_b")
```

### Contradiction Detection

```python
from jarvis_core.contradiction import (
    Claim,
    ContradictionDetector,
    detect_contradiction,
)

detector = ContradictionDetector()

claim_a = Claim(claim_id="1", text="Drug X increases survival", paper_id="A")
claim_b = Claim(claim_id="2", text="Drug X decreases survival", paper_id="B")

result = detector.detect(claim_a, claim_b)
print(f"Contradictory: {result.is_contradictory}")  # True
print(f"Type: {result.contradiction_type.value}")  # "direct"
```

### PRISMA Diagram Generation

```python
from jarvis_core.prisma import PRISMAData, generate_prisma_flow

data = PRISMAData(
    identification_database=1000,
    identification_other=50,
    duplicates_removed=200,
    records_screened=850,
    records_excluded_screening=500,
    full_text_assessed=350,
    full_text_excluded=100,
    studies_included=250,
)

# Generate Mermaid diagram
mermaid = generate_prisma_flow(data, format="mermaid")

# Generate SVG
svg = generate_prisma_flow(data, format="svg")
```

### Active Learning

```python
from jarvis_core.active_learning import (
    ActiveLearningEngine,
    ALConfig,
    UncertaintySampling,
    BudgetStoppingCriterion,
)

config = ALConfig(batch_size=10, initial_sample_size=20)
criterion = BudgetStoppingCriterion(max_labels=100)
engine = ActiveLearningEngine(config=config, stopping_criterion=criterion)

# Initialize with paper embeddings
engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

# Get initial batch for manual labeling
initial_batch = engine.get_initial_batch()

# Update with labels
labels = {pid: is_relevant for pid, is_relevant in user_labels.items()}
engine.update_labels(labels)

# Get next batch (active learning selects most informative)
next_batch = engine.get_next_batch()

# Check stopping
if engine.should_stop():
    results = engine.export_results()
```

### Hybrid Search

```python
from jarvis_core.embeddings import HybridSearch, FusionMethod

search = HybridSearch(
    fusion_method=FusionMethod.RRF,
    bm25_weight=0.4,
    embedding_weight=0.6,
)

search.add_documents([
    {"id": "1", "text": "machine learning medical diagnosis"},
    {"id": "2", "text": "clinical trial results"},
])

results = search.search("ML in medicine", top_k=10)
```

### Paper Scoring

```python
from jarvis_core.paper_scoring import PaperScorer, ScoringWeights

# Custom weights
weights = ScoringWeights(
    evidence_weight=0.4,
    citation_weight=0.3,
    recency_weight=0.2,
    source_weight=0.1,
)

scorer = PaperScorer(weights=weights)

paper = {
    "paper_id": "test_001",
    "title": "A randomized controlled trial",
    "year": 2024,
    "citation_count": 50,
    "source": "pubmed",
}

score = scorer.score(paper, evidence_grade=evidence_grade)
print(f"Overall: {score.overall_score}")
print(f"Evidence: {score.evidence_score}")
```

### Network/Offline Mode

```python
from jarvis_core.network import is_online, degradation_aware

# Check network status
if is_online():
    print("Online mode")
else:
    print("Offline mode")

# Decorator for graceful degradation
@degradation_aware(feature="api_search", fallback=local_search)
def search_papers(query):
    return api.search(query)
```

## REST API

### Base URL

```
http://localhost:8000/api
```

### Authentication

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/runs
```

### Endpoints

#### Health Check

```
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "5.2.0"
}
```

#### List Runs

```
GET /api/runs?limit=20
```

Response:
```json
{
  "status": "success",
  "data": {
    "runs": [
      {
        "run_id": "run_abc123",
        "status": "completed",
        "created_at": "2026-01-09T00:00:00Z",
        "paper_count": 150
      }
    ]
  }
}
```

#### Get Run Details

```
GET /api/runs/{run_id}
```

#### Start New Run

```
POST /api/runs
Content-Type: application/json

{
  "query": "machine learning cancer diagnosis",
  "max_papers": 50,
  "config": {}
}
```

#### Search Corpus

```
GET /api/search?q=query&top_k=20
```

#### Upload Files

```
POST /api/upload/pdf
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf]
```

#### Get KPIs

```
GET /api/kpi
```

Response:
```json
{
  "status": "success",
  "data": {
    "total_papers": 1500,
    "total_runs": 42,
    "avg_processing_time_s": 12.5,
    "evidence_grading_accuracy": 0.87
  }
}
```

### Response Format

All responses follow this structure:

```json
{
  "status": "success",
  "data": { ... },
  "errors": [],
  "warnings": []
}
```

### Error Response

```json
{
  "status": "error",
  "data": null,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Invalid parameter: max_papers must be positive"
    }
  ]
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid token |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 501 | Not Implemented - Feature not available |

## Rate Limits

| Tier | Limit |
|------|-------|
| Default | 100 requests/minute |
| Authenticated | 1000 requests/minute |
| Burst | 20 requests/second |

## Versioning

API version is included in the path: `/api/v1/...`

Current version: `v1`

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Start a run
response = requests.post(
    f"{BASE_URL}/runs",
    json={"query": "diabetes treatment", "max_papers": 100}
)
run_id = response.json()["data"]["run_id"]

# Check status
status = requests.get(f"{BASE_URL}/runs/{run_id}").json()
```

### cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Search
curl "http://localhost:8000/api/search?q=machine+learning&top_k=10"

# Start run
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"query": "cancer diagnosis", "max_papers": 50}'
```

## WebSocket API

For real-time updates:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/runs/{run_id}");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Progress:", data.progress);
};
```

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for API changes.
