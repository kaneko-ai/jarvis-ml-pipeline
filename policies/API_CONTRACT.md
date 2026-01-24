# JARVIS API Contract (Phase 19)

## /api/run [POST]

### Request Body
- `action` (string, required): one of `report`, `paper_fetch`, `oa_search`, `embed`, `index`.
- `query` (string, required): the research query or goal.
- `max_papers` (integer, optional): 1-200. Default: 10.
- `turnstile_token` (string, required): Cloudflare Turnstile token for human verification.

### Constraints
- `action` that is not in the allowlist will return `400 Bad Request`.
- `max_papers` > 200 will be capped at 200.
- `turnstile_token` that fails verification will return `403 Forbidden`.
- Concurrent runs for the same `action` and `query` may be cancelled (handled by GitHub Actions).

## /api/runs [GET]
Returns a proxy to `runs/index.json` hosted on GitHub Pages.
