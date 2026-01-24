# Troubleshooting QA Failures

> Authority: REFERENCE (Level 2, Non-binding)


## Contract tests failing
- Check `schemas/api_map_v1.json` and `schemas/capabilities_v1.json` for missing/extra capabilities.
- Regenerate with `make api-map` and re-run `make test-contract`.
- Verify `dashboard/adapter_manifest.js` endpoints are aligned with the API map.

## API smoke failing
- `/api/health` or `/api/capabilities` returning non-200 means backend is down.
- `/api/runs` returning 501 means the endpoint is not implemented (acceptable for now).
- Validate the `API_BASE` env var for `tests/smoke_api_v1.py`.

## Dashboard E2E failing (mock)
- Ensure the mock server is up (`tests/mock_server/app.py`).
- Check that `DASHBOARD_BASE_URL` and `MOCK_API_BASE` match running ports.
- Use Playwright trace artifacts from CI to pinpoint the failing selector.

## White screen / empty UI
- Confirm the static server is serving `dashboard/` assets.
- Check browser console for failed `fetch` calls to `/api/health` or `/api/runs`.
