# OpsExtract Repository Audit

| Check | Status | Detail |
|---|---|---|
| validate_run_contracts_strict_exists | present | schema_validate.py:def validate_run_contracts_strict |
| orchestrator_calls_strict_validator | present | orchestrator.py uses strict contract validation in write_contract_files stage |
| drive_sync_targets_manifest_outputs | present | drive_sync.py:_target_files_from_manifest references manifest outputs[].path |
| doctor_has_next_commands_section | present | doctor.py writes "## Next Commands" |
| preflight_has_queue_backlog_hard_check | present | preflight.py executes check_sync_queue_backlog with hard=True |
| telemetry_file:models.py | present | jarvis_core\ops_extract\telemetry\models.py |
| telemetry_file:sampler.py | present | jarvis_core\ops_extract\telemetry\sampler.py |
| telemetry_file:progress.py | present | jarvis_core\ops_extract\telemetry\progress.py |
| telemetry_file:eta.py | present | jarvis_core\ops_extract\telemetry\eta.py |

Summary: present=9 missing=0
