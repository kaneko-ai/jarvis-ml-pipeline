"""Artifact store for multi-agent outputs."""

from __future__ import annotations

from pathlib import Path


class ArtifactStore:
    """Persist and retrieve agent artifacts."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path("logs/artifacts")

    def save(self, agent_id: str, filename: str, content: str | bytes) -> str:
        """Save an artifact and return its path."""
        agent_dir = self.base_path / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = agent_dir / filename
        if isinstance(content, bytes):
            artifact_path.write_bytes(content)
        else:
            artifact_path.write_text(content, encoding="utf-8")
        return str(artifact_path)

    def load(self, artifact_path: str) -> str | bytes:
        """Load an artifact (text or binary)."""
        path = Path(artifact_path)
        data = path.read_bytes()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data

    def list_artifacts(self, agent_id: str) -> list[str]:
        """List artifacts for an agent."""
        agent_dir = self.base_path / agent_id
        if not agent_dir.exists():
            return []
        return sorted(str(path) for path in agent_dir.iterdir() if path.is_file())
