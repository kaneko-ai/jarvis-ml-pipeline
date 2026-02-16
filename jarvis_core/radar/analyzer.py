"""Rule-based radar analyzer."""

from __future__ import annotations


TOPIC_RULES = {
    "agent": ["agent", "autonomous", "workflow", "orchestrator"],
    "rag": ["rag", "retrieval", "rerank", "citation"],
    "eval": ["evaluation", "benchmark", "judge", "quality"],
    "ui": ["ui", "dashboard", "visualization", "interface"],
}


def classify_findings(findings: list[dict]) -> list[dict]:
    classified = []
    for finding in findings:
        text = f"{finding.get('title', '')} {finding.get('summary', '')}".lower()
        tags = [
            topic for topic, keywords in TOPIC_RULES.items() if any(k in text for k in keywords)
        ]
        classified.append({**finding, "tags": tags or ["other"]})
    return classified
