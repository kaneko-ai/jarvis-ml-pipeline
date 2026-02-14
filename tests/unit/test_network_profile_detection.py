from __future__ import annotations

from types import SimpleNamespace

from jarvis_core.ops_extract.contracts import OpsExtractConfig
from jarvis_core.ops_extract.network import detect_network_profile


def test_detect_network_profile_online(monkeypatch):
    monkeypatch.delenv("JARVIS_OPS_EXTRACT_FIXED_TIME", raising=False)
    monkeypatch.setattr("socket.gethostbyname", lambda _host: "8.8.8.8")

    def _ok_get(*_args, **_kwargs):
        return SimpleNamespace(status_code=401, content=b"", text="")

    monkeypatch.setattr("requests.get", _ok_get)

    profile, diagnosis = detect_network_profile(OpsExtractConfig(enabled=True))
    assert profile == "ONLINE"
    assert diagnosis["dns_resolve_ok"] is True
    assert diagnosis["drive_api_reachable"] is True


def test_detect_network_profile_offline(monkeypatch):
    monkeypatch.delenv("JARVIS_OPS_EXTRACT_FIXED_TIME", raising=False)

    def _raise_dns(_host):
        raise OSError("dns_error")

    monkeypatch.setattr("socket.gethostbyname", _raise_dns)

    def _raise_get(*_args, **_kwargs):
        raise RuntimeError("network_error")

    monkeypatch.setattr("requests.get", _raise_get)

    profile, diagnosis = detect_network_profile(OpsExtractConfig(enabled=True))
    assert profile == "OFFLINE"
    assert diagnosis["dns_resolve_ok"] is False
