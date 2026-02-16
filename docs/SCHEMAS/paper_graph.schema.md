> Authority: CONTRACT (Level 3, Binding)
> Date: 2026-02-16

# Paper Graph / Radar / Market JSON Schemas

## 1) `paper_graph/tree/graph.json`

```json
{
  "nodes": [
    {
      "node_id": "doi:10.1000/xyz",
      "title": "Paper title",
      "year": 2024,
      "venue": "Nature",
      "ids": {"doi": "10.1000/xyz", "pmid": null, "arxiv": null},
      "level": 0,
      "inbound_cites": 123
    }
  ],
  "edges": [
    {"from_node_id": "doi:10.1000/xyz", "to_node_id": "s2:abc", "type": "cites"}
  ]
}
```

## 2) `paper_graph/map3d/map_points.json`

```json
[
  {
    "paper_id": "arxiv:1234.5678",
    "title": "Root paper",
    "year": 2024,
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "score": 10.0,
    "cluster_id": 0,
    "distance_to_center": 0.0
  }
]
```

## 3) `radar/radar_findings.json`

```json
[
  {
    "source": "arxiv",
    "id": "arxiv:2501.00001",
    "title": "Title",
    "summary": "Short summary",
    "url": "https://arxiv.org/abs/2501.00001",
    "published": "2026-02-15T00:00:00+00:00",
    "tags": ["rag", "eval"]
  }
]
```

## 4) `market/proposals.json`

```json
[
  {
    "idea_id": "idea-1",
    "name": "OA Evidence Tracker",
    "problem": "Problem statement",
    "solution": "Solution statement",
    "why_now": "Timing rationale",
    "risk": "Main risk",
    "differentiation": "Differentiation",
    "sources_used": 12
  }
]
```
