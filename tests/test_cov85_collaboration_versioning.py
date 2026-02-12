from __future__ import annotations

import hashlib

import pytest

from jarvis_core.collaboration.versioning import VersionHistoryStore


def test_version_history_save_list_restore_and_hash() -> None:
    store = VersionHistoryStore()
    v1 = store.save_version("art-1", "hello", "user-a")
    v2 = store.save_version("art-1", "hello world", "user-b")

    versions = store.list_versions("art-1")
    assert [v.id for v in versions] == [v1.id, v2.id]
    assert versions[0].content_hash == hashlib.sha256("hello".encode("utf-8")).hexdigest()

    restored = store.restore_version("art-1", v1.id)
    assert restored == "hello"


def test_version_history_restore_and_diff_errors_and_success() -> None:
    store = VersionHistoryStore()
    v1 = store.save_version("a", "line1\nline2", "u")
    v2 = store.save_version("b", "line1\nline3", "u")

    diff = store.diff_versions(v1.id, v2.id)
    assert "line2" in diff
    assert "line3" in diff

    with pytest.raises(KeyError):
        store.restore_version("a", "missing")

    with pytest.raises(KeyError):
        store.diff_versions(v1.id, "missing")
