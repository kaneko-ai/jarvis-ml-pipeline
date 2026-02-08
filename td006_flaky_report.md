# TD-006 Flaky Test Report

Date: 2026-02-08
Scope: `tests/` (`--ignore=tests/e2e --ignore=tests/integration`)

## Full-suite Reproducibility Check

Command:

```bash
uv run pytest tests/ -x --ignore=tests/e2e --ignore=tests/integration -q
```

Results (3 consecutive runs):

1. `5944 passed, 449 skipped, 207 warnings` in `244.73s`
2. `5944 passed, 449 skipped, 207 warnings` in `268.55s`
3. `5944 passed, 449 skipped, 207 warnings` in `242.62s`

Logs were captured during local verification.

## Targeted Stability Check (Known sensitive tests)

Command:

```bash
uv run pytest \
  tests/test_claim_set_full.py \
  tests/test_td002_scheduler_lyra_health_cov.py::test_health_checker_sync_and_async_paths \
  tests/test_api_map_vs_capabilities.py::test_api_map_vs_capabilities \
  tests/test_figure_extractor.py::test_figure_extractor \
  -q
```

Results (5 consecutive runs):

- All runs: `8 passed, 4 warnings`

## Conclusion

- No flaky behavior was reproduced in this session under the above conditions.
- `TD-006` acceptance for local reproducibility is currently satisfied.
