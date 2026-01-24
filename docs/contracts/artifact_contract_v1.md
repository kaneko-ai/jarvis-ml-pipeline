# Artifact Contract v1

> Authority: CONTRACT (Level 2, Binding)

## Purpose
Define the minimum manifest required to declare a run "successful" across UI/CI/Worker/Local.
This contract fixes the semantics and shape of the artifact manifest so every surface
validates the same output.

## Manifest Location
`schemas/artifact_manifest_v1.schema.json`

## Required Fields
### Top-level
- `run_id` (string)
- `created_at` (string, RFC 3339 date-time)
- `mode` (string enum: `serverless`, `local`)
- `query` (string)
- `pipeline_version` (string)
- `status` (string enum: `queued`, `running`, `success`, `failed`)
- `artifacts` (object)
- `quality` (object)
- `repro` (object)

### `artifacts`
- `summary_json` (string)
- `report_md` (string)
- `stats_json` (string)
- `meta_json` (string)
- `logs_jsonl` (string)

### `quality`
- `papers_found` (integer, >= 0)
- `papers_processed` (integer, >= 0)
- `citations_attached` (boolean)
- `gate_passed` (boolean)
- `gate_reason` (string)

### `repro`
- `query_hash` (string)

## Optional Fields
### `artifacts`
- `corpus_ref` (string)

### `repro`
- `seed` (integer)
- `source_snapshot_ref` (string)

## Success Criteria
A run is only "successful" when:
- `status` is `success`.
- `quality.gate_passed` is `true`.

All required fields must be present and validate against
`schemas/artifact_manifest_v1.schema.json`.
