"""Multi-modal Data Structures (Phase 38).

Defines artifacts for tables and figures extracted from documents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ModalityType(Enum):
    TABLE = "table"
    FIGURE = "figure"
    IMAGE = "image"

@dataclass
class MultiModalArtifact:
    """Base class for non-text artifacts."""
    artifact_id: str
    doc_id: str
    modality: ModalityType
    content: str  # Markdown text or description
    page_number: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "doc_id": self.doc_id,
            "modality": self.modality.value,
            "content": self.content,
            "page_number": self.page_number,
            "metadata": self.metadata
        }

@dataclass
class TableArtifact(MultiModalArtifact):
    """Represents an extracted table."""
    def __init__(self, **kwargs):
        if "modality" not in kwargs:
            kwargs["modality"] = ModalityType.TABLE
        super().__init__(**kwargs)
        # Specific table fields could be added here (e.g. headers, rows)
        # For now, we assume content is Markdown/HTML representation

@dataclass
class FigureArtifact(MultiModalArtifact):
    """Represents an extracted figure/chart."""
    image_path: Optional[str] = None # Path to saved image file

    def __init__(self, image_path: Optional[str] = None, **kwargs):
        if "modality" not in kwargs:
            kwargs["modality"] = ModalityType.FIGURE
        super().__init__(**kwargs)
        self.image_path = image_path

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["image_path"] = self.image_path
        return d
