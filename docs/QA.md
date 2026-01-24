# QA Strategy (P16)

> Authority: REFERENCE (Level 2, Non-binding)


## Test Layers (order matters)
1. **Contract tests**
   - `schemas/api_map_v1.json` vs `schemas/capabilities_v1.json`
   - `dashboard/adapter_manifest.js` vs API map
   - Failure means the API/adapter contract is out of sync.

2. **API smoke tests**
   - `/api/health`, `/api/capabilities`, `/api/runs`, `/api/runs/{id}`, `/api/runs/{id}/files`
   - 501 is allowed for unimplemented endpoints.
   - Failure means the backend is broken.

3. **Dashboard E2E (real server)**
   - Settings → index health → runs → run detail
   - Failure means UI regression.

4. **Dashboard E2E (mock server)**
   - Uses `tests/mock_server` to decouple UI from backend.
   - Failure means fallback/empty-state regression.

## Local Commands
- `make test-contract`
- `make test-smoke`
- `make test-e2e-mock`
- `make test-all`

## Key Artifacts
- Contract sources: `schemas/api_map_v1.json`, `schemas/capabilities_v1.json`
- Adapter manifest: `dashboard/adapter_manifest.js`
- Mock API: `tests/mock_server/app.py`
- E2E: `tests/e2e/dashboard.spec.ts`
