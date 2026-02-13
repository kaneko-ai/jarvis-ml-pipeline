from __future__ import annotations

from jarvis_core.ops_extract.contracts import (
    OPS_EXTRACT_CONFIG_SCHEMA_VERSION,
    build_ops_extract_config,
)


def test_build_ops_extract_config_supports_deprecated_keys():
    cfg = build_ops_extract_config(
        {
            "config_schema_version": "1.0",
            "sync_chunk_size": 1024,
            "drive_api_url": "http://api.local",
            "drive_upload_url": "http://upload.local",
            "trace": False,
            "resume": False,
            "sync": {"enabled": True},
        }
    )
    assert cfg.config_schema_version == "1.0"
    assert cfg.sync_chunk_bytes == 1024
    assert cfg.drive_api_base_url == "http://api.local"
    assert cfg.drive_upload_base_url == "http://upload.local"
    assert cfg.trace_enabled is False
    assert cfg.resume_enabled is False


def test_build_ops_extract_config_defaults_schema_version():
    cfg = build_ops_extract_config({})
    assert cfg.config_schema_version == OPS_EXTRACT_CONFIG_SCHEMA_VERSION
