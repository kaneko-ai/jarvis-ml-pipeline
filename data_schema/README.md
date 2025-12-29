# Data Output Schema (P4)

This document describes the run-level output artifacts generated in `data/runs/{run_id}` for P4.

## Output Directory

```
data/runs/{run_id}/
├── manifest.json
├── research_rank.json
├── notes/
│   ├── 00_RUN_OVERVIEW.md
│   ├── 01_TIER_S.md
│   ├── 02_TIER_A.md
│   ├── papers/
│   │   └── {paper_id}.md
│   └── claims/
│       └── {paper_id}.claims.jsonl
├── claims/
│   └── {paper_id}.claims.jsonl
├── notebooklm/
│   ├── podcast_prompt_1paper.txt
│   ├── podcast_prompt_3to5papers.txt
│   └── podcast_script_outline.md
├── zotero/
│   └── refs.bib
├── logs/
│   └── events_excerpt.jsonl
└── export/
    ├── jarvis_run_{run_id}.zip
    ├── notes_{run_id}.zip
    └── notebooklm_{run_id}.zip
```

## manifest.json

Tracks the outputs generated for reproducibility.

```json
{
  "run_id": "...",
  "manifest_version": "p4-1",
  "generated_at": "ISO8601",
  "template_versions": {
    "obsidian": "p4-obsidian-1.0"
  },
  "generated_outputs": {
    "notes": { "notes_dir": "...", "papers_count": 0, "claims_count": 0 },
    "notebooklm": { "notebooklm_dir": "...", "generated_at": "..." },
    "zotero": ".../refs.bib",
    "research_rank": ".../research_rank.json",
    "logs": ".../logs/events_excerpt.jsonl",
    "package": ".../export/jarvis_run_{run_id}.zip",
    "manifest": ".../manifest.json"
  }
}
```

## research_rank.json

Run-level ranking and tiering of papers.

```json
{
  "run_id": "...",
  "template_version": "p4-obsidian-1.0",
  "generated_at": "ISO8601",
  "rankings": [
    { "paper_id": "...", "score": 0.0, "rank": 1, "tier": "S" }
  ]
}
```

## notes/papers/{paper_id}.md

Obsidian-ready note with YAML frontmatter and required sections:

- TL;DR (200-300 chars)
- Key claims (with evidence locator)
- Methods snapshot
- Results snapshot
- Limitations
- Why it matters
- Evidence map (claim_id → locator → quote)
- Links (Run overview + Obsidian wiki link)

## notes/claims/{paper_id}.claims.jsonl

Claim exports with evidence locator details.

```json
{"paper_id":"...","claim_id":"...","claim_text":"...","evidence":[{"evidence_text":"...","locator":{...}}]}
```

## notebooklm/

- `podcast_prompt_1paper.txt`: single-paper deep dive prompt
- `podcast_prompt_3to5papers.txt`: synthesis prompt for 3-5 papers
- `podcast_script_outline.md`: chapter-level outline

## zotero/

- `refs.bib`: BibTeX export (safe_key format)

## export/

Bundled zip packages. `jarvis_run_{run_id}.zip` includes:

- `manifest.json`
- `notes/`
- `notebooklm/`
- `zotero/`
- `research_rank.json`
- `claims/`
- `logs/`
