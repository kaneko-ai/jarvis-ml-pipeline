"""Artifact version history management."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
import difflib
import uuid


@dataclass
class Version:
    id: str
    artifact_id: str
    content_hash: str
    author: str
    timestamp: str
    content: str


class VersionHistoryStore:
    """In-memory version history store."""

    def __init__(self):
        self._versions: dict[str, list[Version]] = {}

    def save_version(self, artifact_id: str, content: str, author: str) -> Version:
        version_id = str(uuid.uuid4())
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        version = Version(
            id=version_id,
            artifact_id=artifact_id,
            content_hash=content_hash,
            author=author,
            timestamp=datetime.utcnow().isoformat(),
            content=content,
        )
        self._versions.setdefault(artifact_id, []).append(version)
        return version

    def list_versions(self, artifact_id: str) -> list[Version]:
        return list(self._versions.get(artifact_id, []))

    def restore_version(self, artifact_id: str, version_id: str) -> str:
        version = next(
            (v for v in self._versions.get(artifact_id, []) if v.id == version_id),
            None,
        )
        if not version:
            raise KeyError(f"Version not found: {version_id}")
        return version.content

    def diff_versions(self, version_id_1: str, version_id_2: str) -> str:
        all_versions = [v for versions in self._versions.values() for v in versions]
        v1 = next((v for v in all_versions if v.id == version_id_1), None)
        v2 = next((v for v in all_versions if v.id == version_id_2), None)
        if not v1 or not v2:
            raise KeyError("One or both versions not found")
        diff = difflib.unified_diff(
            v1.content.splitlines(),
            v2.content.splitlines(),
            fromfile=version_id_1,
            tofile=version_id_2,
        )
        return "\n".join(diff)