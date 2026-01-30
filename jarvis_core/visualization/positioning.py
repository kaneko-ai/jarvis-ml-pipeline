"""3D Positioning / Spatial Projection.

Per RP31, this projects papers to interpretable 3D space.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def project_to_3d(paper: PaperVector) -> tuple[float, float, float]:
    """Project paper to 3D space using BiologicalAxisVector.

    Axes (fixed):
        X: immune_activation (-1 suppressive to +1 active)
        Y: metabolism_signal (-1 metabolic to +1 signaling)
        Z: tumor_context (-1 systemic to +1 TME/local)

    Args:
        paper: The PaperVector to project.

    Returns:
        3D coordinates (x, y, z).
    """
    return paper.biological_axis.as_tuple()


def project_all_to_3d(
    papers: list[PaperVector],
) -> list[dict]:
    """Project all papers to 3D space with metadata.

    Args:
        papers: List of PaperVectors.

    Returns:
        List of dicts with coordinates and paper info.
    """
    results = []
    for paper in papers:
        x, y, z = project_to_3d(paper)
        results.append(
            {
                "paper_id": paper.paper_id,
                "source_locator": paper.source_locator,
                "x": x,
                "y": y,
                "z": z,
                "year": paper.metadata.year,
                "top_concept": (
                    paper.concept.top_concepts(1)[0][0] if paper.concept.concepts else None
                ),
            }
        )
    return results


def get_position_description(paper: PaperVector) -> str:
    """Get human-readable position description.

    Args:
        paper: The PaperVector.

    Returns:
        Description of paper's position in research space.
    """
    bio = paper.biological_axis
    parts = []

    if bio.immune_activation > 0.3:
        parts.append("免疫活性化領域")
    elif bio.immune_activation < -0.3:
        parts.append("免疫抑制領域")
    else:
        parts.append("免疫中立")

    if bio.metabolism_signal > 0.3:
        parts.append("シグナル重視")
    elif bio.metabolism_signal < -0.3:
        parts.append("代謝重視")

    if bio.tumor_context > 0.3:
        parts.append("TME局所研究")
    elif bio.tumor_context < -0.3:
        parts.append("全身免疫研究")

    return "、".join(parts) if parts else "標準領域"