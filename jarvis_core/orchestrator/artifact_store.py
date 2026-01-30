"""Artifact storage for orchestrator agents."""

from __future__ import annotations

from pathlib import Path


class ArtifactStore:
    """Save and load agent artifacts under logs/artifacts."""

    def __init__(self, base_dir: Path | str = Path("logs/artifacts")) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, agent_id: str, filename: str, content: str | bytes) -> str:
        agent_dir = self.base_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = agent_dir / filename
        if isinstance(content, bytes):
            artifact_path.write_bytes(content)
        else:
            artifact_path.write_text(content, encoding="utf-8")
        return str(artifact_path)

    def load(self, artifact_path: str) -> str | bytes:
        path = Path(artifact_path)
        data = path.read_bytes()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data

    def list_artifacts(self, agent_id: str) -> list[str]:
        agent_dir = self.base_dir / agent_id
        if not agent_dir.exists():
            return []
        return [str(path) for path in sorted(agent_dir.iterdir()) if path.is_file()]