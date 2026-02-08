> Authority: SPEC (Level 1, Binding)

# Bundle Contract v1

This contract defines the required files for a JARVIS run bundle.

## Required files (10)

1. `input.json`
2. `papers.jsonl`
3. `claims.jsonl`
4. `evidence.jsonl`
5. `scores.json`
6. `report.md`
7. `warnings.jsonl`
8. `eval_summary.json`
9. `cost_report.json`
10. `provenance.jsonl`

## Validation rules

- Every required file must exist.
- Every required file must be non-empty.
- `*.json` files must be parseable JSON objects.
- `*.jsonl` files must contain valid JSON per non-empty line.

## Notes

- This file is the canonical contract for `scripts/validate_bundle.py`.
- Contract checks in CI should fail on missing or invalid required files.


