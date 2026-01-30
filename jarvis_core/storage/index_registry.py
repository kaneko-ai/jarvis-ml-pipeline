"""Index Registry - manages index manifests."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class IndexRegistry:
    """Manages index versions and manifests.

    Structure:
        data/index/
            ├── index_manifest.json
            ├── v1/
            ├── v2/
            └── ...
    """

    def __init__(self, base_dir: str = "data/index"):
        self.base_dir = Path(base_dir)
        self.manifest_path = self.base_dir / "index_manifest.json"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_manifest(self) -> dict | None:
        """Get current manifest."""
        if self.manifest_path.exists():
            with open(self.manifest_path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def get_current_version(self) -> str | None:
        """Get current index version."""
        manifest = self.get_manifest()
        return manifest.get("current_version") if manifest else None

    def register(
        self,
        version: str,
        source: str,
        doc_count: int,
        build_args: dict | None = None,
    ) -> dict:
        """Register a new index version.

        Args:
            version: Version string (e.g., "v1", "20241221")
            source: Data source description
            doc_count: Number of documents indexed
            build_args: Build arguments used

        Returns:
            Updated manifest.
        """
        manifest = self.get_manifest() or {"versions": []}

        entry = {
            "version": version,
            "created_at": datetime.now().isoformat(),
            "source": source,
            "doc_count": doc_count,
            "build_args": build_args or {},
        }

        manifest["versions"].append(entry)
        manifest["current_version"] = version
        manifest["updated_at"] = datetime.now().isoformat()

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    def get_version_info(self, version: str) -> dict | None:
        """Get info for a specific version."""
        manifest = self.get_manifest()
        if manifest:
            for v in manifest.get("versions", []):
                if v["version"] == version:
                    return v
        return None

    def has_index(self) -> bool:
        """Check if any index exists."""
        return self.manifest_path.exists() and self.get_current_version() is not None