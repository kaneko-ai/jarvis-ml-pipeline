window.JARVIS_ADAPTER_MANIFEST = {
  "apiMapVersion": "v1",
  "endpoints": {
    "health": "/api/health",
    "capabilities": "/api/capabilities",
    "runs": "/api/runs",
    "runDetail": "/api/runs/{id}",
    "runFiles": "/api/runs/{id}/files",
    "runFile": "/api/runs/{id}/files/{path}",
    "researchRank": "/api/research/rank",
    "qaReport": "/api/qa/report",
    "submissionDecision": "/api/submission/decision",
    "financeForecast": "/api/finance/forecast"
  },
  "capabilities": [
    "health",
    "capabilities",
    "runs",
    "runs.detail",
    "runs.files",
    "runs.files.download",
    "research.rank",
    "qa.report",
    "submission.decision",
    "finance.forecast"
  ]
};
