"""Bundle v2 Specification.

Per V4-D1, this implements the new bundle format with:
- Artifact + Provenance
- Scoring registry snapshot
- Evidence chunks
- Audit report
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, TYPE_CHECKING

from .artifacts.schema import ArtifactBase, Provenance
from .audit.report import generate_audit_report, AuditReport

if TYPE_CHECKING:
    from .paper_vector import PaperVector


class BundleV2:
    """Bundle v2 format for research outputs."""

    VERSION = "2.0"

    def __init__(self):
        self.artifacts: List[ArtifactBase] = []
        self.vectors: List["PaperVector"] = []
        self.evidence_chunks: Dict[str, str] = {}
        self.scoring_snapshot: Dict[str, Any] = {}
        self.created_at: datetime = datetime.now()
        self.metadata: Dict[str, Any] = {}

    def add_artifact(self, artifact: ArtifactBase) -> None:
        """Add an artifact to the bundle."""
        self.artifacts.append(artifact)

    def add_vector(self, vector: "PaperVector") -> None:
        """Add a paper vector to the bundle."""
        self.vectors.append(vector)

    def add_evidence(self, chunk_id: str, text: str) -> None:
        """Add evidence chunk."""
        self.evidence_chunks[chunk_id] = text

    def set_scoring_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Set scoring registry snapshot."""
        self.scoring_snapshot = snapshot

    def generate_audit(self) -> List[AuditReport]:
        """Generate audit reports for all artifacts."""
        return [generate_audit_report(a) for a in self.artifacts]

    def export(self, output_dir: str) -> str:
        """Export bundle to directory.

        Creates:
        - bundle.json (main artifact data)
        - evidence/ (chunk files)
        - vectors/ (paper vectors)
        - audit.md (audit report)
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # 1. bundle.json
        bundle_data = {
            "version": self.VERSION,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "scoring_snapshot": self.scoring_snapshot,
        }
        with open(out_path / "bundle.json", "w", encoding="utf-8") as f:
            json.dump(bundle_data, f, indent=2, ensure_ascii=False)

        # 2. evidence/
        evidence_dir = out_path / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        for chunk_id, text in self.evidence_chunks.items():
            with open(evidence_dir / f"{chunk_id}.txt", "w", encoding="utf-8") as f:
                f.write(text)

        # 3. vectors/
        vectors_dir = out_path / "vectors"
        vectors_dir.mkdir(exist_ok=True)
        for i, v in enumerate(self.vectors):
            with open(vectors_dir / f"vector_{i}.json", "w", encoding="utf-8") as f:
                json.dump(v.to_dict(), f, indent=2, ensure_ascii=False)

        # 4. audit.md
        audit_reports = self.generate_audit()
        audit_lines = ["# Bundle Audit Report", "", f"**Generated**: {datetime.now().isoformat()}", ""]

        for report in audit_reports:
            audit_lines.append(report.to_markdown())
            audit_lines.append("")
            audit_lines.append("---")
            audit_lines.append("")

        with open(out_path / "audit.md", "w", encoding="utf-8") as f:
            f.write("\n".join(audit_lines))

        return str(out_path)

    @classmethod
    def load(cls, bundle_path: str) -> "BundleV2":
        """Load bundle from directory."""
        path = Path(bundle_path)
        bundle = cls()

        # Load bundle.json
        bundle_file = path / "bundle.json"
        if bundle_file.exists():
            with open(bundle_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                bundle.metadata = data.get("metadata", {})
                bundle.scoring_snapshot = data.get("scoring_snapshot", {})
                bundle.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))

        # Load evidence
        evidence_dir = path / "evidence"
        if evidence_dir.exists():
            for chunk_file in evidence_dir.glob("*.txt"):
                chunk_id = chunk_file.stem
                bundle.evidence_chunks[chunk_id] = chunk_file.read_text(encoding="utf-8")

        return bundle


def create_bundle_v2(
    artifacts: List[ArtifactBase],
    vectors: List["PaperVector"] = None,
    metadata: Dict[str, Any] = None,
) -> BundleV2:
    """Factory function to create Bundle v2.

    Args:
        artifacts: List of artifacts.
        vectors: Optional paper vectors.
        metadata: Optional metadata.

    Returns:
        BundleV2 instance.
    """
    bundle = BundleV2()

    for a in artifacts:
        bundle.add_artifact(a)

    if vectors:
        for v in vectors:
            bundle.add_vector(v)

    if metadata:
        bundle.metadata = metadata

    # Capture scoring snapshot
    from .scoring.registry import ScoreRegistry
    registry = ScoreRegistry()
    bundle.set_scoring_snapshot({
        "registered_scores": registry.list_scores(),
        "version": BundleV2.VERSION,
    })

    return bundle
