# Release Checklist (P16)

1. **Contract checks**
   - `make api-map`
   - Commit any diff in `schemas/api_map_v1.json`.

2. **API smoke**
   - `make test-smoke`
   - Ensure `/api/health` and `/api/capabilities` are 200.

3. **Mock E2E**
   - `make test-e2e-mock`
   - Verifies dashboard flow against `tests/mock_server`.

4. **UI sanity**
   - Open the dashboard (GitHub Pages or static host).
   - Navigate: Settings → Health → Runs → Run detail.

5. **If something fails**
   - Follow `docs/TROUBLESHOOTING.md`.
